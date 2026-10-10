import hashlib
import hmac
from datetime import timedelta

from django.utils import timezone

from orders import services
from orders.models import Order

CHECKOUT = "/orders/api/checkout/"


def make_order(auth_client, product, shipping, qty=1):
    r = auth_client.post(CHECKOUT, {**shipping, "items": [{"product_id": product.id, "quantity": qty}]}, format="json")
    return r.data


def pay(auth_client, order_id, payment_id="pay_1", signature="mock_success"):
    return auth_client.post(f"/orders/api/orders/{order_id}/pay/", {"payment_id": payment_id, "signature": signature}, format="json")


def test_checkout_response_has_payment_info(auth_client, phone, shipping):
    data = make_order(auth_client, phone, shipping, 2)
    assert data["payment"]["provider"] == "mock" and data["payment"]["amount"] == 20000  # paise


def test_valid_payment_marks_order_paid(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    r = pay(auth_client, order["id"])
    assert r.status_code == 200 and r.data["status"] == "PAID"
    assert pay(auth_client, order["id"]).data["status"] == "PAID"  # repeat is harmless


def test_bad_signature_does_not_pay(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    r = pay(auth_client, order["id"], signature="forged")
    assert r.status_code == 400
    assert Order.objects.get(pk=order["id"]).status == "PENDING"


def test_cancel_restores_stock_and_blocks_payment(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping, 3)
    phone.refresh_from_db(); assert phone.stock == 2
    assert auth_client.post(f"/orders/api/orders/{order['id']}/cancel/").data["status"] == "CANCELLED"
    phone.refresh_from_db(); assert phone.stock == 5
    assert pay(auth_client, order["id"]).status_code == 409


def test_paid_order_cannot_be_cancelled(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    pay(auth_client, order["id"])
    assert auth_client.post(f"/orders/api/orders/{order['id']}/cancel/").status_code == 409


def test_expiry_releases_stock_of_old_unpaid_orders_only(auth_client, phone, shipping):
    old = make_order(auth_client, phone, shipping, 2)
    paid = make_order(auth_client, phone, shipping, 1)
    pay(auth_client, paid["id"])
    Order.objects.update(created_at=timezone.now() - timedelta(hours=2))
    assert services.expire_pending_orders() == 1
    assert Order.objects.get(pk=old["id"]).status == "CANCELLED"
    assert Order.objects.get(pk=paid["id"]).status == "PAID"
    phone.refresh_from_db(); assert phone.stock == 4  # 5 - 1 (paid) ; the 2 came back


def test_razorpay_signature_check(settings, auth_client, user, shipping):
    settings.PAYMENT_PROVIDER = "razorpay"
    settings.RAZORPAY_KEY_SECRET = "test_secret"
    # create the order directly so the test never calls Razorpay's real API
    order = Order.objects.create(user=user, total_amount=100, provider_order_id="order_ABC", **shipping)
    good = hmac.new(b"test_secret", b"order_ABC|pay_XYZ", hashlib.sha256).hexdigest()
    assert pay(auth_client, order.id, "pay_XYZ", "0" * 64).status_code == 400
    r = pay(auth_client, order.id, "pay_XYZ", good)
    assert r.status_code == 200 and r.data["status"] == "PAID"
