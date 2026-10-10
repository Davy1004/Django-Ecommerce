"""All business rules of checkout live here, away from HTTP, so they are easy to test.

Key ideas
* The server decides prices and totals - the client only says WHAT and HOW MANY.
* Everything that touches stock happens in ONE database transaction.
* Products are locked (SELECT ... FOR UPDATE) in id order, so two buyers can't both
  take the last item, and two checkouts can't deadlock each other.
"""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from products.models import Product

from .models import Order, OrderItem
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


@transaction.atomic
def _create_order(user, items, shipping, idempotency_key):
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
    order.total_amount = total
    order.save(update_fields=["total_amount"])
    return order


def place_order(*, user, items, shipping, idempotency_key=None):
    """Returns (order, created). Calling again with the same idempotency key returns
    the original order instead of charging / reserving stock twice."""
    if idempotency_key:
        existing = Order.objects.filter(user=user, idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
    try:
        order = _create_order(user, items, shipping, idempotency_key)
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
        cancel_order(order)
        raise
    order.payment_provider = info["provider"]
    order.provider_order_id = info["provider_order_id"]
    order.save(update_fields=["payment_provider", "provider_order_id", "updated_at"])
    return order, True


@transaction.atomic
def cancel_order(order):
    """Cancel an unpaid order and give its stock back."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == Order.Status.CANCELLED:
        return order
    if order.status != Order.Status.PENDING:
        raise OrderNotPayable("Only unpaid orders can be cancelled.")
    for item in order.items.select_related("product").order_by("product_id"):
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
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
    return order


def expire_pending_orders(now=None):
    """Cancel unpaid orders older than the TTL so abandoned carts don't lock stock forever."""
    cutoff = (now or timezone.now()) - timedelta(minutes=settings.PENDING_ORDER_TTL_MINUTES)
    cancelled = 0
    for order in Order.objects.filter(status=Order.Status.PENDING, created_at__lt=cutoff):
        cancel_order(order)
        cancelled += 1
    return cancelled
