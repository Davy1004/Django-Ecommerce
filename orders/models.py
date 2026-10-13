from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Coupon(models.Model):
    class Kind(models.TextChoices):
        PERCENT = "PERCENT", "Percent off"
        FIXED = "FIXED", "Fixed amount off"

    code = models.CharField(max_length=40, unique=True, help_text="Stored upper-case; customers can type it in any case.")
    description = models.CharField(max_length=200, blank=True)
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.PERCENT)
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percent (e.g. 10) or rupees (e.g. 200).")
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Cap for percent coupons.")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Total redemptions allowed; empty = unlimited.")
    used_count = models.PositiveIntegerField(default=0, editable=False)
    once_per_user = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(value__gt=0), name="coupon_value_gt_0"),
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending payment"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)

    # shipping details
    name = models.CharField(max_length=200)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    # subtotal = sum of the lines; total_amount = subtotal - discount_amount (what the customer pays)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    coupon_code = models.CharField(max_length=40, blank=True)  # snapshot, survives coupon deletion
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # payment bookkeeping
    payment_provider = models.CharField(max_length=20, blank=True)
    provider_order_id = models.CharField(max_length=100, blank=True)
    provider_payment_id = models.CharField(max_length=100, blank=True)

    # Lets the client safely retry a checkout request (double click, flaky network)
    idempotency_key = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "idempotency_key"], name="uniq_order_user_idempotency_key"),
        ]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT, related_name="+")
    # Snapshots: if the product is renamed or re-priced later, old orders must not change.
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name="orderitem_quantity_gt_0")]

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
