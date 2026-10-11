import json

from events.models import PaymentEvent
from events.parsing import sign

SECRET = "test-webhook-secret"
URL = "/events/webhook/"


def post_event(client, body, signature=None, secret=SECRET):
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    sig = sign(raw, secret) if signature is None else signature
    return client.post(URL, data=raw, content_type="application/json", HTTP_X_WEBHOOK_SIGNATURE=sig)


def captured_body(provider_order_id, event_id="evt_1", payment_id="pay_1", event_type="payment.captured"):
    return {"id": event_id, "type": event_type, "order_id": provider_order_id, "payment_id": payment_id}


def queue_event(provider_order_id, event_id="evt_1", payment_id="pay_1", event_type="payment.captured", **extra):
    """Put an event straight into the queue table (what the webhook view does after verifying)."""
    return PaymentEvent.objects.create(
        provider="mock", event_id=event_id, event_type=event_type, provider_order_id=provider_order_id,
        payment_id=payment_id, payload=captured_body(provider_order_id, event_id, payment_id, event_type), **extra)
