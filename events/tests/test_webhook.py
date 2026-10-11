import json

import pytest

from events.models import PaymentEvent
from events.parsing import sign

from .helpers import SECRET, URL, captured_body, post_event


def test_valid_webhook_is_stored_as_new(client):
    r = post_event(client, captured_body("mock_order_7", "evt_a", "pay_9"))
    assert r.status_code == 200 and r.data["status"] == "accepted"
    e = PaymentEvent.objects.get()
    assert (e.status, e.attempts, e.event_id) == ("NEW", 0, "evt_a")
    assert (e.event_type, e.provider_order_id, e.payment_id) == ("payment.captured", "mock_order_7", "pay_9")


def test_the_same_event_delivered_twice_is_stored_once(client):
    body = captured_body("mock_order_7", "evt_a")
    assert post_event(client, body).data["status"] == "accepted"
    r = post_event(client, body)
    assert r.status_code == 200 and r.data["status"] == "duplicate"  # 2xx so the provider stops retrying
    assert PaymentEvent.objects.count() == 1


def test_wrong_signature_is_rejected_and_nothing_stored(client):
    r = post_event(client, captured_body("mock_order_7"), secret="not-the-real-secret")
    assert r.status_code == 400
    assert PaymentEvent.objects.count() == 0


def test_missing_signature_is_rejected(client):
    raw = json.dumps(captured_body("mock_order_7")).encode()
    r = client.post(URL, data=raw, content_type="application/json")
    assert r.status_code == 400 and PaymentEvent.objects.count() == 0


def test_body_changed_after_signing_is_rejected(client):
    signed_for = json.dumps(captured_body("mock_order_7", payment_id="pay_1")).encode()
    tampered = json.dumps(captured_body("mock_order_7", payment_id="pay_EVIL")).encode()
    r = post_event(client, tampered, signature=sign(signed_for, SECRET))
    assert r.status_code == 400 and PaymentEvent.objects.count() == 0


def test_endpoint_refuses_everything_when_no_secret_is_configured(client, settings):
    settings.WEBHOOK_SECRET = ""
    r = post_event(client, captured_body("mock_order_7"))
    assert r.status_code == 503 and PaymentEvent.objects.count() == 0


def test_signed_but_malformed_bodies_are_rejected(client):
    assert post_event(client, b"not json").status_code == 400
    assert post_event(client, b"[1, 2]").status_code == 400
    assert post_event(client, {"type": "payment.captured"}).status_code == 400  # no id
    assert PaymentEvent.objects.count() == 0


def test_razorpay_shaped_webhook_is_parsed(client, settings):
    settings.PAYMENT_PROVIDER = "razorpay"
    raw = json.dumps({
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_RZ1", "order_id": "order_RZ1", "status": "captured"}}},
    }).encode()
    r = client.post(URL, data=raw, content_type="application/json",
                    HTTP_X_RAZORPAY_SIGNATURE=sign(raw, SECRET), HTTP_X_RAZORPAY_EVENT_ID="evt_rz_1")
    assert r.status_code == 200
    e = PaymentEvent.objects.get()
    assert (e.provider, e.event_id, e.provider_order_id, e.payment_id) == ("razorpay", "evt_rz_1", "order_RZ1", "pay_RZ1")


def test_razorpay_webhook_without_event_id_header_is_rejected(client, settings):
    settings.PAYMENT_PROVIDER = "razorpay"
    raw = json.dumps({"event": "payment.captured", "payload": {}}).encode()
    r = client.post(URL, data=raw, content_type="application/json", HTTP_X_RAZORPAY_SIGNATURE=sign(raw, SECRET))
    assert r.status_code == 400
