from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from orders import services
from orders.models import Coupon, Order
from products.models import Product

CHECKOUT = "/orders/api/checkout/"
VALIDATE = "/orders/api/coupons/validate/"


def body(shipping, *items, coupon=None):
    d = {**shipping, "items": [{"product_id": p.id, "quantity": q} for p, q in items]}
    if coupon is not None:
        d["coupon_code"] = coupon
    return d


@pytest.fixture
def ten(db):
    return Coupon.objects.create(code="welcome10", kind="PERCENT", value=10, description="10% off")


def test_code_is_stored_upper_case(ten):
    assert ten.code == "WELCOME10"


def test_percent_discount_applied_server_side(auth_client, phone, shipping, ten):
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 2), coupon="welcome10"), format="json")  # 200.00
    assert r.status_code == 201
    assert Decimal(str(r.data["subtotal"])) == Decimal("200.00")
    assert Decimal(str(r.data["discount_amount"])) == Decimal("20.00")
    assert Decimal(str(r.data["total_amount"])) == Decimal("180.00")
    assert r.data["coupon_code"] == "WELCOME10"
    ten.refresh_from_db()
    assert ten.used_count == 1


def test_payment_amount_is_the_discounted_total(auth_client, phone, shipping, ten):
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 2), coupon="WELCOME10"), format="json")
    assert r.data["payment"]["amount"] == 18000  # paise


def test_fixed_discount_and_cap(auth_client, phone, shipping):
    Coupon.objects.create(code="CAP", kind="PERCENT", value=50, max_discount=Decimal("30"))
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 2), coupon="CAP"), format="json")
    assert Decimal(str(r.data["discount_amount"])) == Decimal("30.00")  # 50% would be 100


def test_total_never_below_one_rupee(db):
    c = Coupon.objects.create(code="HUGE", kind="FIXED", value=Decimal("9999"))
    assert services.calculate_discount(c, Decimal("100.00")) == Decimal("99.00")


def test_unknown_code(auth_client, phone, shipping):
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 1), coupon="NOPE"), format="json")
    assert r.status_code == 400 and "does not exist" in r.data["error"]
    phone.refresh_from_db()
    assert phone.stock == 5 and Order.objects.count() == 0  # rolled back, nothing reserved


@pytest.mark.parametrize("kwargs,msg", [
    ({"is_active": False}, "no longer active"),
    ({"valid_until": timezone.now() - timedelta(days=1)}, "expired"),
    ({"valid_from": timezone.now() + timedelta(days=1)}, "not valid yet"),
    ({"min_order_amount": Decimal("500")}, "or more"),
    ({"max_uses": 1, "used_count": 1}, "fully redeemed"),
])
def test_invalid_coupons(auth_client, phone, shipping, kwargs, msg):
    Coupon.objects.create(code="X1", kind="PERCENT", value=10, **kwargs)
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 1), coupon="x1"), format="json")
    assert r.status_code == 400 and msg in r.data["error"]


def test_once_per_user(auth_client, phone, shipping, ten):
    assert auth_client.post(CHECKOUT, body(shipping, (phone, 1), coupon="WELCOME10"), format="json").status_code == 201
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 1), coupon="WELCOME10"), format="json")
    assert r.status_code == 400 and "already used" in r.data["error"]


def test_cancelling_gives_the_redemption_back(auth_client, phone, shipping, ten):
    order_id = auth_client.post(CHECKOUT, body(shipping, (phone, 1), coupon="WELCOME10"), format="json").data["id"]
    assert auth_client.post(f"/orders/api/orders/{order_id}/cancel/").status_code == 200
    ten.refresh_from_db()
    assert ten.used_count == 0
    # and the same user can use it again
    assert auth_client.post(CHECKOUT, body(shipping, (phone, 1), coupon="WELCOME10"), format="json").status_code == 201


def test_expired_pending_order_releases_coupon(auth_client, phone, shipping, ten, settings):
    auth_client.post(CHECKOUT, body(shipping, (phone, 1), coupon="WELCOME10"), format="json")
    Order.objects.update(created_at=timezone.now() - timedelta(days=1))
    assert services.expire_pending_orders() == 1
    ten.refresh_from_db()
    assert ten.used_count == 0


def test_last_redemption_goes_to_only_one_buyer(auth_client, phone, shipping, django_user_model):
    from rest_framework.test import APIClient
    Coupon.objects.create(code="ONE", kind="PERCENT", value=10, max_uses=1)
    django_user_model.objects.create_user("bo", "bo@example.com", "s3cret-pass-99")
    other = APIClient()
    tok = other.post("/accounts/api/login/", {"username": "bo", "password": "s3cret-pass-99"}, format="json").data["access"]
    other.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}")
    assert auth_client.post(CHECKOUT, body(shipping, (phone, 1), coupon="ONE"), format="json").status_code == 201
    assert other.post(CHECKOUT, body(shipping, (phone, 1), coupon="ONE"), format="json").status_code == 400


def test_validate_endpoint_previews_without_redeeming(auth_client, phone, ten):
    r = auth_client.post(VALIDATE, {"code": "welcome10", "items": [{"product_id": phone.id, "quantity": 3}]}, format="json")
    assert r.status_code == 200
    assert (Decimal(str(r.data["discount"])), Decimal(str(r.data["total"]))) == (Decimal("30.00"), Decimal("270.00"))
    ten.refresh_from_db()
    assert ten.used_count == 0 and Order.objects.count() == 0


def test_validate_requires_login_and_reports_errors(client, auth_client, phone):
    payload = {"code": "NOPE", "items": [{"product_id": phone.id, "quantity": 1}]}
    assert client.post(VALIDATE, payload, format="json").status_code == 401
    assert auth_client.post(VALIDATE, payload, format="json").status_code == 400


def test_orders_without_coupon_unchanged(auth_client, phone, shipping):
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 1)), format="json")
    assert Decimal(str(r.data["discount_amount"])) == 0 and r.data["coupon_code"] == ""
    assert Decimal(str(r.data["total_amount"])) == Decimal(str(r.data["subtotal"]))
