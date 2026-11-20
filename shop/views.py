from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.db.models import Q
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.units import mm

from .models import Category, Product, Order, OrderItem, Wishlist


# =========================================================
# HOME + SEARCH + CATEGORY FILTER
# =========================================================

def home(request):

    search_query = request.GET.get("q", "").strip()
    category_name = request.GET.get("category", "").strip()

    products = Product.objects.filter(
        is_active=True
    ).select_related("category")

    selected_category = None

    if category_name:

        selected_category = Category.objects.filter(
            name__iexact=category_name
        ).first()

        if selected_category:
            products = products.filter(category=selected_category)
        else:
            products = products.none()

    if search_query:

        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    products = products.distinct().order_by("id")

    if selected_category and not search_query:
        products = products[:8]

    categories = Category.objects.all()

    wishlist_product_ids = []

    if request.user.is_authenticated:

        wishlist_product_ids = list(
            Wishlist.objects.filter(
                user=request.user
            ).values_list(
                "product_id",
                flat=True
            )
        )

    context = {
        "products": products,
        "categories": categories,
        "search_query": search_query,
        "selected_category": selected_category,
        "selected_category_name": (
            selected_category.name if selected_category else category_name
        ),
        "wishlist_product_ids": wishlist_product_ids,
    }

    return render(request, "home.html", context)


# =========================================================
# PRODUCT DETAIL + 360 DEGREE VIEW
# LOGIN REQUIRED
# =========================================================

@login_required(login_url="login")
def product_detail(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    view_360_images = product.view_360_images.all()

    return render(
        request,
        "product_detail.html",
        {
            "product": product,
            "view_360_images": view_360_images,
        }
    )


# =========================================================
# ADD TO CART
# =========================================================

def add_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    cart = request.session.get("cart", {})

    product_id = str(product_id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    try:
        current_quantity = int(cart.get(product_id, 0))
    except (TypeError, ValueError):
        current_quantity = 0

    new_quantity = current_quantity + quantity

    if new_quantity > product.stock:
        new_quantity = product.stock

    if new_quantity > 0:
        cart[product_id] = new_quantity
    else:
        cart.pop(product_id, None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


# =========================================================
# CART PAGE
# =========================================================

def cart(request):

    cart_data = request.session.get("cart", {})

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():

        product = Product.objects.filter(
            id=product_id,
            is_active=True
        ).first()

        if product:

            subtotal = product.price * quantity
            total += subtotal

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            })

    context = {
        "cart_items": cart_items,
        "total": total,
    }

    return render(request, "cart.html", context)


# =========================================================
# UPDATE CART QUANTITY
# =========================================================

def update_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    cart = request.session.get("cart", {})

    product_id = str(product_id)

    action = request.POST.get("action")

    try:
        current_quantity = int(cart.get(product_id, 0))
    except (TypeError, ValueError):
        current_quantity = 0

    if action == "increase":

        if current_quantity < product.stock:
            cart[product_id] = current_quantity + 1

    elif action == "decrease":

        if current_quantity > 1:
            cart[product_id] = current_quantity - 1
        else:
            cart.pop(product_id, None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


# =========================================================
# REMOVE FROM CART
# =========================================================

def remove_from_cart(request, product_id):

    cart = request.session.get("cart", {})

    product_id = str(product_id)

    cart.pop(product_id, None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


# =========================================================
# CHECKOUT
# =========================================================

def checkout(request):

    cart_data = request.session.get("cart", {})

    if not cart_data:
        return redirect("cart")

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():

        product = Product.objects.filter(
            id=product_id,
            is_active=True
        ).first()

        if product:

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                continue

            if quantity < 1:
                continue

            subtotal = product.price * quantity
            total += subtotal

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            })

    if not cart_items:
        return redirect("cart")

    if request.method == "POST":

        customer_name = request.POST.get("customer_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()

        payment_method = request.POST.get("payment_method", "").strip()
        transaction_id = request.POST.get("transaction_id", "").strip()
        payment_screenshot = request.FILES.get("payment_screenshot")

        # VALIDATE CUSTOMER DETAILS

        if not all([
            customer_name,
            email,
            phone,
            address,
            city,
            state,
            pincode
        ]):

            messages.error(request, "Please fill all delivery details.")
            return redirect("checkout")

        # VALIDATE PAYMENT METHOD

        if payment_method not in ["UPI", "COD"]:

            messages.error(request, "Please select a valid payment method.")
            return redirect("checkout")

        # VALIDATE UPI REFERENCE

        if payment_method == "UPI" and not transaction_id:

            messages.error(
                request,
                "Please enter your UPI transaction reference number."
            )

            return redirect("checkout")

        # CREATE ORDER

        with transaction.atomic():

            locked_items = []

            # RECHECK STOCK

            for item in cart_items:

                product = Product.objects.select_for_update().filter(
                    id=item["product"].id,
                    is_active=True
                ).first()

                if not product or product.stock < item["quantity"]:

                    messages.error(
                        request,
                        f"Insufficient stock for {item['product'].name}."
                    )

                    return redirect("cart")

                locked_items.append({
                    "product": product,
                    "quantity": item["quantity"],
                })

            # ORDER STATUS

            order_status = (
                "Confirmed" if payment_method == "COD" else "Pending"
            )

            # PAYMENT STATUS

            payment_status = "Pending"

            # CREATE ORDER

            order = Order.objects.create(

                customer_name=customer_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                pincode=pincode,

                total_amount=total,

                payment_method=payment_method,

                transaction_id=(
                    transaction_id if payment_method == "UPI" else ""
                ),

                payment_screenshot=(
                    payment_screenshot if payment_method == "UPI" else None
                ),

                payment_status=payment_status,
                status=order_status,
            )

            # CREATE ORDER ITEMS + UPDATE STOCK

            for item in locked_items:

                product = item["product"]
                quantity = item["quantity"]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )

                product.stock -= quantity
                product.save(update_fields=["stock"])

        # CLEAR CART

        request.session["cart"] = {}
        request.session.modified = True

        return redirect("order_success", order_id=order.id)

    context = {
        "cart_items": cart_items,
        "total": total,
    }

    return render(request, "checkout.html", context)


# =========================================================
# ORDER SUCCESS
# =========================================================

def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    return render(
        request,
        "order_success.html",
        {
            "order": order
        }
    )


# =========================================================
# DOWNLOAD ORDER RECEIPT PDF
# =========================================================

def download_order_receipt(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'attachment; filename="HomeDecor_Receipt_{order.id}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()

    elements = []

    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#8B6B55"),
        alignment=1,
        fontSize=22,
        spaceAfter=10
    )

    normal_style = styles["Normal"]

    elements.append(Paragraph("HOME DECOR", title_style))

    elements.append(
        Paragraph("ORDER RECEIPT", styles["Heading2"])
    )

    elements.append(Spacer(1, 12))

    # CUSTOMER DETAILS

    elements.append(Paragraph(
        f"<b>Order Number:</b> #{order.id}",
        normal_style
    ))

    elements.append(Paragraph(
        f"<b>Customer Name:</b> {escape(str(order.customer_name))}",
        normal_style
    ))

    elements.append(Paragraph(
        f"<b>Email:</b> {escape(str(order.email))}",
        normal_style
    ))

    elements.append(Paragraph(
        f"<b>Mobile:</b> {escape(str(order.phone))}",
        normal_style
    ))

    elements.append(Paragraph(
        f"<b>Delivery Address:</b> "
        f"{escape(str(order.address))}, "
        f"{escape(str(order.city))}, "
        f"{escape(str(order.state))}, "
        f"PIN: {escape(str(order.pincode))}",
        normal_style
    ))

    elements.append(Paragraph(
        f"<b>Payment Method:</b> "
        f"{escape(str(order.get_payment_method_display()))}",
        normal_style
    ))

    elements.append(Paragraph(
        f"<b>Payment Status:</b> {escape(str(order.payment_status))}",
        normal_style
    ))

    elements.append(Paragraph(
        f"<b>Order Status:</b> {escape(str(order.status))}",
        normal_style
    ))

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph("ORDER ITEMS", styles["Heading2"])
    )

    # ORDER ITEM TABLE

    data = [
        ["Product", "Qty", "Price", "Subtotal"]
    ]

    order_items = order.items.all()

    for item in order_items:

        product_name = (
            item.product.name if item.product else "Product unavailable"
        )

        data.append([
            Paragraph(escape(str(product_name)), normal_style),
            str(item.quantity),
            f"Rs. {item.price}",
            f"Rs. {item.price * item.quantity}"
        ])

    table = Table(
        data,
        colWidths=[75*mm, 20*mm, 35*mm, 35*mm]
    )

    table.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8B6B55")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

    ]))

    elements.append(table)

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            f"<b>Order Total: Rs. {order.total_amount}</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 20))

    # PAYMENT NOTE

    if order.payment_method == "UPI":

        if order.payment_status == "Pending":

            note = (
                "UPI payment details submitted. "
                "Payment confirmation is subject to verification."
            )

        else:

            note = "UPI payment status: Paid."

    else:

        if order.payment_status == "Pending":

            note = "Cash on Delivery. Payment is due at delivery."

        else:

            note = "Cash on Delivery payment has been recorded as Paid."

    elements.append(
        Paragraph(escape(note), normal_style)
    )

    elements.append(Spacer(1, 25))

    elements.append(
        Paragraph(
            "Thank you for shopping with Home Decor!",
            title_style
        )
    )

    doc.build(elements)

    return response


# =========================================================
# CUSTOMER SIGNUP
# =========================================================

def signup(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not username or not email or not password:

            messages.error(
                request,
                "Please fill all required fields."
            )

            return redirect("signup")

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("signup")

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("signup")

        if User.objects.filter(email=email).exists():

            messages.error(
                request,
                "Email already registered."
            )

            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)

        return redirect("home")

    return render(request, "signup.html")


# =========================================================
# CUSTOMER LOGIN
# =========================================================

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            next_url = (
                request.POST.get("next")
                or request.GET.get("next")
            )

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()}
            ):

                return redirect(next_url)

            return redirect("home")

        messages.error(
            request,
            "Invalid username or password."
        )

        return redirect("login")

    return render(request, "login.html")


# =========================================================
# CUSTOMER LOGOUT
# =========================================================

def logout_view(request):

    logout(request)

    return redirect("home")


# =========================================================
# ADD / REMOVE WISHLIST
# =========================================================

def toggle_wishlist(request, product_id):

    if not request.user.is_authenticated:

        return JsonResponse({
            "success": False,
            "login_required": True,
            "login_url": reverse("login")
        }, status=401)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()

    if wishlist_item:

        wishlist_item.delete()

        added = False
        message = f"{product.name} removed from wishlist."

    else:

        Wishlist.objects.create(
            user=request.user,
            product=product
        )

        added = True
        message = f"{product.name} added to wishlist."

    wishlist_count = Wishlist.objects.filter(
        user=request.user
    ).count()

    return JsonResponse({
        "success": True,
        "added": added,
        "product_id": product.id,
        "wishlist_count": wishlist_count,
        "message": message
    })


# =========================================================
# WISHLIST PAGE
# =========================================================

def wishlist(request):

    if not request.user.is_authenticated:
        return redirect("login")

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related(
        "product",
        "product__category"
    )

    context = {
        "wishlist_items": wishlist_items,
    }

    return render(request, "wishlist.html", context)