"""All business rules of checkout live here, away from HTTP, so they are easy to test.

Key ideas
* The server decides prices and totals - the client only says WHAT and HOW MANY.
* Everything that touches stock happens in ONE database transaction.
* Products are locked (SELECT ... FOR UPDATE) in id order, so two buyers can't both
  take the last item, and two checkouts can't deadlock each other.
"""
from collections import defaultdict
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from products.models import Product

from .models import Coupon, Order, OrderItem
from . import emails
from .payments import get_provider


class CheckoutError(Exception):
    status_code = 400

    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class ProductUnavailable(CheckoutError):
    status_code = 400


class InsufficientStock(CheckoutError):
    status_code = 409


class OrderNotPayable(CheckoutError):
    status_code = 409


class PaymentVerificationFailed(CheckoutError):
    status_code = 400


class OrderNotFound(CheckoutError):
    status_code = 404


class CouponInvalid(CheckoutError):
    status_code = 400


CENT = Decimal("0.01")
MIN_PAYABLE = Decimal("1.00")  # payment providers cannot charge zero


def calculate_discount(coupon, subtotal):
    """Pure maths: how much `coupon` takes off `subtotal`. Never lets the total drop below Rs 1."""
    if coupon.kind == Coupon.Kind.PERCENT:
        discount = (subtotal * coupon.value / 100).quantize(CENT, rounding=ROUND_HALF_UP)
        if coupon.max_discount is not None:
            discount = min(discount, coupon.max_discount)
    else:
        discount = coupon.value
    return max(Decimal("0"), min(discount, subtotal - MIN_PAYABLE)).quantize(CENT)


def check_coupon(coupon, *, user, subtotal, now=None):
    """Raise CouponInvalid with a customer-friendly reason, or return the discount."""
    now = now or timezone.now()
    if not coupon.is_active:
        raise CouponInvalid("This coupon is no longer active.")
    if coupon.valid_from and now < coupon.valid_from:
        raise CouponInvalid("This coupon is not valid yet.")
    if coupon.valid_until and now > coupon.valid_until:
        raise CouponInvalid("This coupon has expired.")
    if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
        raise CouponInvalid("This coupon has been fully redeemed.")
    if subtotal < coupon.min_order_amount:
        raise CouponInvalid(f"Add items worth \u20b9{coupon.min_order_amount:g} or more to use this coupon.")
    if coupon.once_per_user and Order.objects.filter(user=user, coupon=coupon).exclude(status=Order.Status.CANCELLED).exists():
        raise CouponInvalid("You have already used this coupon.")
    return calculate_discount(coupon, subtotal)


def find_coupon(code, *, lock=False):
    qs = Coupon.objects.select_for_update() if lock else Coupon.objects
    coupon = qs.filter(code=(code or "").strip().upper()).first()
    if coupon is None:
        raise CouponInvalid("That coupon code does not exist.")
    return coupon


def price_items(items):
    """Server-side subtotal for a cart (used by the coupon preview endpoint)."""
    wanted = defaultdict(int)
    for item in items:
        wanted[item["product_id"]] += item["quantity"]
    products = {p.id: p for p in Product.objects.filter(id__in=wanted, is_active=True)}
    missing = sorted(set(wanted) - set(products))
    if missing:
        raise ProductUnavailable("Some products are not available.", {"product_ids": missing})
    return sum((products[pid].price * qty for pid, qty in wanted.items()), Decimal("0"))


def preview_coupon(*, user, code, items):
    subtotal = price_items(items)
    coupon = find_coupon(code)
    discount = check_coupon(coupon, user=user, subtotal=subtotal)
    return {"code": coupon.code, "description": coupon.description, "subtotal": subtotal,
            "discount": discount, "total": subtotal - discount}


@transaction.atomic
def _create_order(user, items, shipping, idempotency_key, coupon_code=""):
    wanted = defaultdict(int)  # the same product listed twice is merged
    for item in items:
        wanted[item["product_id"]] += item["quantity"]

    locked = Product.objects.select_for_update().filter(id__in=wanted, is_active=True).order_by("id")
    products = {p.id: p for p in locked}

    missing = sorted(set(wanted) - set(products))
    if missing:
        raise ProductUnavailable("Some products are not available.", {"product_ids": missing})

    short = [
        {"product_id": pid, "name": products[pid].name, "requested": qty, "available": products[pid].stock}
        for pid, qty in sorted(wanted.items()) if products[pid].stock < qty
    ]
    if short:
        raise InsufficientStock("Not enough stock for some items.", short)

    order = Order.objects.create(user=user, idempotency_key=idempotency_key, **shipping)
    lines, total = [], Decimal("0")
    for pid in sorted(wanted):
        product, qty = products[pid], wanted[pid]
        Product.objects.filter(pk=pid).update(stock=F("stock") - qty)
        lines.append(OrderItem(order=order, product=product, product_name=product.name,
                               unit_price=product.price, quantity=qty))
        total += product.price * qty
    OrderItem.objects.bulk_create(lines)
    discount, coupon = Decimal("0"), None
    if coupon_code:
        coupon = find_coupon(coupon_code, lock=True)  # row lock: two buyers can't both take the last redemption
        discount = check_coupon(coupon, user=user, subtotal=total)
        Coupon.objects.filter(pk=coupon.pk).update(used_count=F("used_count") + 1)
    order.subtotal, order.discount_amount, order.total_amount = total, discount, total - discount
    order.coupon, order.coupon_code = coupon, coupon.code if coupon else ""
    order.save(update_fields=["subtotal", "discount_amount", "total_amount", "coupon", "coupon_code"])
    return order


def place_order(*, user, items, shipping, idempotency_key=None, coupon_code=""):
    """Returns (order, created). Calling again with the same idempotency key returns
    the original order instead of charging / reserving stock twice."""
    if idempotency_key:
        existing = Order.objects.filter(user=user, idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
    try:
        order = _create_order(user, items, shipping, idempotency_key, coupon_code)
    except IntegrityError:
        # two identical requests raced; the database's unique constraint picked one winner
        if idempotency_key:
            existing = Order.objects.filter(user=user, idempotency_key=idempotency_key).first()
            if existing:
                return existing, False
        raise

    # Talking to the payment provider happens OUTSIDE the DB transaction (it's a slow
    # network call and must not hold row locks).
    try:
        info = get_provider().create_payment(order)
    except Exception:
        cancel_order(order, notify=False)  # the customer never saw this order
        raise
    order.payment_provider = info["provider"]
    order.provider_order_id = info["provider_order_id"]
    order.save(update_fields=["payment_provider", "provider_order_id", "updated_at"])
    return order, True


@transaction.atomic
def cancel_order(order, notify=True):
    """Cancel an unpaid order and give its stock back."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == Order.Status.CANCELLED:
        return order
    if order.status != Order.Status.PENDING:
        raise OrderNotPayable("Only unpaid orders can be cancelled.")
    for item in order.items.select_related("product").order_by("product_id"):
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
    if order.coupon_id:  # a cancelled order gives its coupon redemption back
        Coupon.objects.filter(pk=order.coupon_id, used_count__gt=0).update(used_count=F("used_count") - 1)
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    if notify:
        transaction.on_commit(lambda: emails.send_order_email(order.pk, "cancelled"))
    return order


@transaction.atomic
def confirm_payment(*, order_id, user, payment_id, signature):
    try:
        order = Order.objects.select_for_update().get(pk=order_id, user=user)
    except Order.DoesNotExist:
        raise CheckoutError("Order not found.") from None
    if order.status == Order.Status.PAID:
        return order  # confirming twice is harmless
    if order.status == Order.Status.CANCELLED:
        raise OrderNotPayable("This order was cancelled (it may have expired). Please order again.")
    if not get_provider().verify(order, payment_id, signature):
        raise PaymentVerificationFailed("Payment verification failed.")
    order.status = Order.Status.PAID
    order.provider_payment_id = payment_id
    order.save(update_fields=["status", "provider_payment_id", "updated_at"])
    transaction.on_commit(lambda: emails.send_order_email(order.pk, "paid"))
    return order


@transaction.atomic
def settle_payment(*, provider_order_id, payment_id):
    """Mark an order paid because the payment PROVIDER told us so (webhook).

    No user/signature argument: the webhook's own signature was already checked before the
    event was stored. Safe to call many times for the same payment.
    """
    order = Order.objects.select_for_update().filter(provider_order_id=provider_order_id).first()
    if order is None:
        raise OrderNotFound(f"No order with provider id {provider_order_id!r} (yet).")
    if order.status == Order.Status.PAID:
        return order
    if order.status == Order.Status.CANCELLED:
        raise OrderNotPayable(f"Order #{order.pk} was cancelled but payment {payment_id} was captured - refund needed.")
    order.status = Order.Status.PAID
    order.provider_payment_id = payment_id
    order.save(update_fields=["status", "provider_payment_id", "updated_at"])
    transaction.on_commit(lambda: emails.send_order_email(order.pk, "paid"))
    return order


def expire_pending_orders(now=None):
    """Cancel unpaid orders older than the TTL so abandoned carts don't lock stock forever."""
    cutoff = (now or timezone.now()) - timedelta(minutes=settings.PENDING_ORDER_TTL_MINUTES)
    cancelled = 0
    for order in Order.objects.filter(status=Order.Status.PENDING, created_at__lt=cutoff):
        cancel_order(order)
        cancelled += 1
    return cancelled
