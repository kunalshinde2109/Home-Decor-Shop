from django.contrib import admin
from .models import Category, Product, Product360Image, Order, OrderItem, Wishlist


# =====================================================
# CATEGORY ADMIN
# =====================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# =====================================================
# PRODUCT 360 IMAGE ADMIN
# =====================================================

class Product360ImageInline(admin.TabularInline):
    model = Product360Image
    extra = 1


# =====================================================
# PRODUCT ADMIN
# =====================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "category",
        "price",
        "stock",
        "is_new",
        "is_sale",
        "is_active",
    )

    list_filter = (
        "category",
        "is_new",
        "is_sale",
        "is_active",
    )

    search_fields = ("name", "description")

    inlines = [Product360ImageInline]


# =====================================================
# ORDER ITEM INLINE
# =====================================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price")


# =====================================================
# ORDER ADMIN
# =====================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer_name",
        "phone",
        "total_amount",
        "payment_method",
        "payment_status",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_method",
        "payment_status",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "email",
        "phone",
    )

    readonly_fields = ("created_at",)

    inlines = [OrderItemInline]


# =====================================================
# WISHLIST ADMIN
# =====================================================

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "product", "created_at")

    search_fields = ("user__username", "product__name")

    list_filter = ("created_at",)