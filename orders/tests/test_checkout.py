from decimal import Decimal

import pytest

from orders.models import Order
from products.models import Product

CHECKOUT = "/orders/api/checkout/"


def body(shipping, *items):
    return {**shipping, "items": [{"product_id": p.id, "quantity": q} for p, q in items]}


def test_checkout_requires_login(client, phone, shipping):
    assert client.post(CHECKOUT, body(shipping, (phone, 1)), format="json").status_code == 401


def test_server_computes_total_and_reduces_stock(auth_client, phone, laptop, shipping):
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 2), (laptop, 1)), format="json")
    assert r.status_code == 201
    assert Decimal(str(r.data["total_amount"])) == Decimal("450.50")  # 2*100 + 250.50
    assert r.data["status"] == "PENDING" and len(r.data["items"]) == 2
    phone.refresh_from_db(); laptop.refresh_from_db()
    assert (phone.stock, laptop.stock) == (3, 1)


def test_client_cannot_set_price_or_total(auth_client, phone, shipping):
    payload = body(shipping, (phone, 1))
    payload["total_amount"] = 1          # ignored
    payload["items"][0]["price"] = 0.01  # ignored
    r = auth_client.post(CHECKOUT, payload, format="json")
    assert Decimal(str(r.data["total_amount"])) == Decimal("100.00")


def test_not_enough_stock_is_409_and_nothing_changes(auth_client, phone, laptop, shipping):
    # laptop has only 2; the phone line is fine - the whole order must roll back
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 1), (laptop, 3)), format="json")
    assert r.status_code == 409
    assert r.data["details"][0]["available"] == 2
    phone.refresh_from_db()
    assert phone.stock == 5 and Order.objects.count() == 0


def test_cannot_oversell_the_last_items(auth_client, phone, shipping):
    assert auth_client.post(CHECKOUT, body(shipping, (phone, 5)), format="json").status_code == 201
    assert auth_client.post(CHECKOUT, body(shipping, (phone, 1)), format="json").status_code == 409
    phone.refresh_from_db()
    assert phone.stock == 0


def test_duplicate_lines_are_merged(auth_client, phone, shipping):
    payload = body(shipping, (phone, 2), (phone, 1))
    r = auth_client.post(CHECKOUT, payload, format="json")
    assert r.status_code == 201 and len(r.data["items"]) == 1 and r.data["items"][0]["quantity"] == 3


@pytest.mark.parametrize("bad", [
    {"items": []},
    {"items": [{"product_id": 1, "quantity": 0}]},
    {"items": [{"product_id": 1, "quantity": -2}]},
])
def test_validation_errors(auth_client, shipping, bad):
    r = auth_client.post(CHECKOUT, {**shipping, **bad}, format="json")
    assert r.status_code == 400 and "error" in r.data


def test_unknown_or_inactive_product(auth_client, phone, shipping):
    phone.is_active = False; phone.save()
    r = auth_client.post(CHECKOUT, body(shipping, (phone, 1)), format="json")
    assert r.status_code == 400


def test_idempotency_key_prevents_double_order(auth_client, phone, shipping):
    payload = body(shipping, (phone, 1))
    a = auth_client.post(CHECKOUT, payload, format="json", HTTP_IDEMPOTENCY_KEY="abc-123")
    b = auth_client.post(CHECKOUT, payload, format="json", HTTP_IDEMPOTENCY_KEY="abc-123")
    assert a.status_code == 201 and b.status_code == 200
    assert a.data["id"] == b.data["id"] and Order.objects.count() == 1
    phone.refresh_from_db()
    assert phone.stock == 4  # reserved once, not twice


def test_snapshot_survives_price_change(auth_client, phone, shipping):
    order_id = auth_client.post(CHECKOUT, body(shipping, (phone, 1)), format="json").data["id"]
    Product.objects.filter(pk=phone.pk).update(price="999.00", name="Renamed")
    item = auth_client.get(f"/orders/api/orders/{order_id}/").data["items"][0]
    assert item["product_name"] == "Phone" and Decimal(str(item["unit_price"])) == Decimal("100.00")


def test_users_only_see_their_own_orders(auth_client, client, phone, shipping, django_user_model):
    order_id = auth_client.post(CHECKOUT, body(shipping, (phone, 1)), format="json").data["id"]
    django_user_model.objects.create_user("eve", "e@example.com", "another-pass-77")
    token = client.post("/accounts/api/login/", {"username": "eve", "password": "another-pass-77"}, format="json").data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.get("/orders/api/orders/").data == []
    assert client.get(f"/orders/api/orders/{order_id}/").status_code == 404
    assert client.post(f"/orders/api/orders/{order_id}/cancel/").status_code == 404
