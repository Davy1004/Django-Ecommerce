"""Turn a raw webhook request into a normalised event - or reject it.

Rule #1 of webhooks: anyone on the internet can POST to your URL. The ONLY thing proving it
came from the provider is the HMAC signature over the raw body, made with a shared secret.
We verify it before storing anything, and compare in constant time.
"""
import hashlib
import hmac
import json
from dataclasses import dataclass

from django.conf import settings


class WebhookRejected(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ParsedEvent:
    provider: str
    event_id: str
    event_type: str
    provider_order_id: str
    payment_id: str
    payload: dict


def sign(raw_body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()


def _check_signature(raw_body, signature):
    if not settings.WEBHOOK_SECRET:
        raise WebhookRejected("Webhook receiver is not configured.", 503)  # fail closed
    if not signature or not hmac.compare_digest(sign(raw_body, settings.WEBHOOK_SECRET), signature):
        raise WebhookRejected("Invalid signature.")


def _load_json(raw_body):
    try:
        data = json.loads(raw_body)
    except ValueError:
        raise WebhookRejected("Body is not valid JSON.") from None
    if not isinstance(data, dict):
        raise WebhookRejected("Body must be a JSON object.")
    return data


def _parse_mock(headers, raw_body):
    _check_signature(raw_body, headers.get("X-Webhook-Signature"))
    data = _load_json(raw_body)
    event_id, event_type = data.get("id"), data.get("type")
    if not event_id or not event_type:
        raise WebhookRejected("Event needs 'id' and 'type'.")
    return ParsedEvent("mock", str(event_id), str(event_type), str(data.get("order_id", "")),
                       str(data.get("payment_id", "")), data)


def _parse_razorpay(headers, raw_body):
    # Razorpay signs the raw body with the webhook secret and sends the event id in a header.
    _check_signature(raw_body, headers.get("X-Razorpay-Signature"))
    data = _load_json(raw_body)
    event_id, event_type = headers.get("X-Razorpay-Event-Id"), data.get("event")
    if not event_id or not event_type:
        raise WebhookRejected("Missing event id or type.")
    entity = ((data.get("payload") or {}).get("payment") or {}).get("entity") or {}
    return ParsedEvent("razorpay", event_id, event_type, entity.get("order_id", ""), entity.get("id", ""), data)


def parse_webhook(headers, raw_body: bytes) -> ParsedEvent:
    parser = _parse_razorpay if settings.PAYMENT_PROVIDER == "razorpay" else _parse_mock
    return parser(headers, raw_body)
