"""Payment providers behind one tiny interface.

create_payment(order) -> dict the client needs to start paying
verify(order, payment_id, signature) -> bool

* MockProvider needs no account: great for demos and tests.
* RazorpayProvider uses Razorpay *test mode* keys (free, no real money).
"""
import hashlib
import hmac
from decimal import Decimal

from django.conf import settings


def to_paise(amount: Decimal) -> int:
    return int((Decimal(amount) * 100).quantize(Decimal("1")))


class MockProvider:
    name = "mock"
    SUCCESS_SIGNATURE = "mock_success"

    def create_payment(self, order):
        return {"provider": self.name, "provider_order_id": f"mock_order_{order.pk}"}

    def public_info(self, order):
        return {"provider": self.name, "provider_order_id": order.provider_order_id,
                "amount": to_paise(order.total_amount), "currency": "INR"}

    def verify(self, order, payment_id, signature):
        return bool(payment_id) and signature == self.SUCCESS_SIGNATURE


class RazorpayProvider:
    name = "razorpay"

    def _client(self):
        import razorpay  # imported lazily so the mock provider needs no extra package
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    def create_payment(self, order):
        rp_order = self._client().order.create({
            "amount": to_paise(order.total_amount),
            "currency": "INR",
            "receipt": f"order_{order.pk}",
        })
        return {"provider": self.name, "provider_order_id": rp_order["id"]}

    def public_info(self, order):
        return {"provider": self.name, "provider_order_id": order.provider_order_id,
                "amount": to_paise(order.total_amount), "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID}

    def verify(self, order, payment_id, signature):
        # Razorpay signs "<order_id>|<payment_id>" with your secret (HMAC-SHA256).
        # Only someone holding the secret can produce a valid signature, so a client
        # cannot fake "I paid".
        message = f"{order.provider_order_id}|{payment_id}".encode()
        expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")


def get_provider():
    return RazorpayProvider() if settings.PAYMENT_PROVIDER == "razorpay" else MockProvider()
