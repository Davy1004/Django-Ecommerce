from django.contrib import admin

from .models import Coupon, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "unit_price", "quantity"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "total_amount", "created_at"]
    list_filter = ["status"]
    search_fields = ["id", "user__username", "email"]
    readonly_fields = ["subtotal", "discount_amount", "coupon", "coupon_code", "total_amount", "provider_order_id", "provider_payment_id", "idempotency_key"]
    inlines = [OrderItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "kind", "value", "min_order_amount", "used_count", "max_uses", "valid_until", "is_active"]
    list_filter = ["kind", "is_active"]
    search_fields = ["code", "description"]
