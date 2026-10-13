import pytest
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from orders import services
from orders.models import Coupon, Order

CHECKOUT = "/orders/api/checkout/"


def place(auth_client, shipping, phone, **extra):
    r = auth_client.post(CHECKOUT, {**shipping, "items": [{"product_id": phone.id, "quantity": 2}], **extra}, format="json")
    assert r.status_code == 201
    return r.data["id"]


def pay(auth_client, oid):
    return auth_client.post(f"/orders/api/orders/{oid}/pay/", {"payment_id": f"mock_pay_{oid}", "signature": "mock_success"}, format="json")


def test_confirmation_email_on_payment(auth_client, shipping, phone, django_capture_on_commit_callbacks):
    oid = place(auth_client, shipping, phone)
    assert mail.outbox == []  # placing an order alone sends nothing
    with django_capture_on_commit_callbacks(execute=True):
        assert pay(auth_client, oid).status_code == 200
    assert len(mail.outbox) == 1
    m = mail.outbox[0]
    assert m.to == ["asha@example.com"] and f"#{oid}" in m.subject
    assert "Total paid: Rs 200.00" in m.body and f"/orders/{oid}" in m.body
    assert m.alternatives and "text/html" in m.alternatives[0][1]


def test_paying_twice_sends_one_email(auth_client, shipping, phone, django_capture_on_commit_callbacks):
    oid = place(auth_client, shipping, phone)
    with django_capture_on_commit_callbacks(execute=True):
        pay(auth_client, oid)
        pay(auth_client, oid)
    assert len(mail.outbox) == 1


def test_email_shows_discount(auth_client, shipping, phone, django_capture_on_commit_callbacks):
    Coupon.objects.create(code="TEN", kind="PERCENT", value=10)
    oid = place(auth_client, shipping, phone, coupon_code="ten")
    with django_capture_on_commit_callbacks(execute=True):
        pay(auth_client, oid)
    assert "Discount (TEN): -Rs 20.00" in mail.outbox[0].body and "Total paid: Rs 180.00" in mail.outbox[0].body


def test_cancel_and_expiry_send_cancelled_email(auth_client, shipping, phone, django_capture_on_commit_callbacks):
    oid = place(auth_client, shipping, phone)
    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(f"/orders/api/orders/{oid}/cancel/")
    assert len(mail.outbox) == 1 and "cancelled" in mail.outbox[0].subject
    oid2 = place(auth_client, shipping, phone)
    Order.objects.filter(pk=oid2).update(created_at=timezone.now() - timedelta(days=1))
    with django_capture_on_commit_callbacks(execute=True):
        services.expire_pending_orders()
    assert len(mail.outbox) == 2


def test_mail_failure_does_not_break_payment(auth_client, shipping, phone, settings, django_capture_on_commit_callbacks):
    settings.EMAIL_BACKEND = "tests_missing.backend"  # sending will raise
    oid = place(auth_client, shipping, phone)
    with django_capture_on_commit_callbacks(execute=True):
        r = pay(auth_client, oid)
    assert r.status_code == 200 and Order.objects.get(pk=oid).status == "PAID"
