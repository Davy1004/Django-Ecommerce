from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from orders.models import Coupon, Order

CHECKOUT = "/orders/api/checkout/"
URL = "/api/admin/sales/"


@pytest.fixture
def staff_client(django_user_model):
    django_user_model.objects.create_user("boss", "boss@example.com", "s3cret-pass-99", is_staff=True)
    c = APIClient()
    tok = c.post("/accounts/api/login/", {"username": "boss", "password": "s3cret-pass-99"}, format="json").data["access"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}")
    return c


def order(auth_client, shipping, product, qty, pay=True, **extra):
    oid = auth_client.post(CHECKOUT, {**shipping, "items": [{"product_id": product.id, "quantity": qty}], **extra}, format="json").data["id"]
    if pay:
        auth_client.post(f"/orders/api/orders/{oid}/pay/", {"payment_id": "p", "signature": "mock_success"}, format="json")
    return oid


def test_only_staff_can_see_it(client, auth_client):
    assert client.get(URL).status_code == 401
    assert auth_client.get(URL).status_code == 403


def test_empty_shop_returns_zeros(staff_client):
    d = staff_client.get(URL).data
    assert d["totals"]["revenue"] == 0 and d["totals"]["paid_orders"] == 0 and d["range"]["orders"] == 0
    assert len(d["daily"]) == 30 and d["top_products"] == [] and d["totals"]["orders_by_status"] == {"PENDING": 0, "PAID": 0, "CANCELLED": 0}


def test_revenue_counts_paid_orders_only(staff_client, auth_client, shipping, phone, laptop):
    order(auth_client, shipping, phone, 2)                     # paid  200
    order(auth_client, shipping, laptop, 1)                    # paid  250.50
    order(auth_client, shipping, phone, 1, pay=False)          # pending
    cancelled = order(auth_client, shipping, phone, 1, pay=False)
    auth_client.post(f"/orders/api/orders/{cancelled}/cancel/")
    d = staff_client.get(URL).data
    assert d["totals"]["revenue"] == pytest.approx(450.50)
    assert d["totals"]["paid_orders"] == 2 and d["totals"]["units_sold"] == 3
    assert d["totals"]["average_order_value"] == pytest.approx(225.25)
    assert d["totals"]["orders_by_status"] == {"PENDING": 1, "PAID": 2, "CANCELLED": 1}
    assert d["range"]["revenue"] == pytest.approx(450.50)
    assert d["daily"][-1]["revenue"] == pytest.approx(450.50) and d["daily"][-1]["orders"] == 2
    assert [p["name"] for p in d["top_products"]] == ["Laptop", "Phone"]
    assert d["by_category"][0]["category"] == "Gadgets"


def test_old_orders_leave_the_range_but_stay_in_totals(staff_client, auth_client, shipping, phone):
    oid = order(auth_client, shipping, phone, 1)
    Order.objects.filter(pk=oid).update(created_at=timezone.now() - timedelta(days=60))
    d = staff_client.get(URL + "?days=30").data
    assert d["range"]["revenue"] == 0 and d["totals"]["revenue"] == pytest.approx(100)
    assert staff_client.get(URL + "?days=90").data["range"]["revenue"] == pytest.approx(100)


def test_coupon_usage_and_discounts(staff_client, auth_client, shipping, phone):
    Coupon.objects.create(code="TEN", kind="PERCENT", value=10)
    order(auth_client, shipping, phone, 2, coupon_code="TEN")
    d = staff_client.get(URL).data
    assert d["totals"]["discounts_given"] == pytest.approx(20)
    assert d["coupons"] == [{"code": "TEN", "orders": 1, "discount": 20.0}]


def test_low_stock_list_is_lowest_first(staff_client, phone, laptop):
    d = staff_client.get(URL).data
    assert [(p["slug"], p["stock"]) for p in d["low_stock"]] == [("laptop", 2), ("phone", 5)]


def test_me_exposes_is_staff(staff_client, auth_client):
    assert staff_client.get("/accounts/api/me/").data["is_staff"] is True
    assert auth_client.get("/accounts/api/me/").data["is_staff"] is False


def test_ensure_admin_creates_updates_and_skips(db, monkeypatch, django_user_model):
    call_command("ensure_admin")  # nothing set -> no user
    assert django_user_model.objects.count() == 0
    monkeypatch.setenv("ADMIN_USERNAME", "root1")
    monkeypatch.setenv("ADMIN_PASSWORD", "first-pass-123")
    call_command("ensure_admin")
    u = django_user_model.objects.get(username="root1")
    assert u.is_staff and u.is_superuser and u.check_password("first-pass-123")
    monkeypatch.setenv("ADMIN_PASSWORD", "second-pass-456")  # rotating the env var rotates the password
    call_command("ensure_admin")
    u.refresh_from_db()
    assert u.check_password("second-pass-456") and django_user_model.objects.count() == 1
