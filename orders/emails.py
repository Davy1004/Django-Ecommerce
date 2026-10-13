"""Transactional emails. Sending never breaks the request that triggered it: a mail-server
outage is logged, the order still goes through."""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Order

log = logging.getLogger(__name__)


def _send(order, template, subject):
    context = {
        "order": order,
        "items": list(order.items.all()),
        "shop": settings.SHOP_NAME,
        "order_url": f"{settings.FRONTEND_URL}/orders/{order.pk}",
    }
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string(f"orders/{template}.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    message.attach_alternative(render_to_string(f"orders/{template}.html", context), "text/html")
    message.send()


def send_order_email(order_id, kind):
    """kind: 'paid' | 'cancelled'. Safe to call from transaction.on_commit."""
    try:
        order = Order.objects.prefetch_related("items").get(pk=order_id)
        if kind == "paid":
            _send(order, "email_paid", f"Order #{order.pk} confirmed - thank you!")
        elif kind == "cancelled":
            _send(order, "email_cancelled", f"Order #{order.pk} was cancelled")
    except Exception:  # noqa: BLE001 - deliberately broad, see module docstring
        log.exception("Could not send %s email for order %s", kind, order_id)
