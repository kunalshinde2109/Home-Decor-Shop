from django.db import models
from django.contrib.auth.models import User


# =====================================================
# CATEGORY
# =====================================================

class Category(models.Model):

    name = models.CharField(
        max_length=100
    )

    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


# =====================================================
# PRODUCT
# =====================================================

class Product(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    name = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to="products/"
    )

    # 360 DEGREE VIEW
    has_360_view = models.BooleanField(
        default=False,
        help_text="Enable 360 degree product viewer"
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    is_new = models.BooleanField(
        default=False
    )

    is_sale = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# =====================================================
# PRODUCT 360 IMAGES
# =====================================================

class Product360Image(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="view_360_images"
    )

    image = models.ImageField(
        upload_to="products/360/"
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Image order: 1, 2, 3, 4..."
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.product.name} - 360 {self.order}"


# =====================================================
# ORDER
# =====================================================

class Order(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("UPI", "Online Payment (UPI)"),
        ("COD", "Cash on Delivery"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
    ]

    customer_name = models.CharField(
        max_length=100
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=15
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    pincode = models.CharField(
        max_length=10
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # PAYMENT METHOD
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default="COD"
    )

    # UPI TRANSACTION ID
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # PAYMENT SCREENSHOT
    payment_screenshot = models.ImageField(
        upload_to="payments/",
        blank=True,
        null=True
    )

    # PAYMENT STATUS
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending"
    )

    # ORDER STATUS
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


# =====================================================
# ORDER ITEM
# =====================================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.product} x {self.quantity}"


# =====================================================
# WISHLIST
# =====================================================

class Wishlist(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_wishlist"
            )
        ]

        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"