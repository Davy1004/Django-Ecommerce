from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from events import processing
from events.models import PaymentEvent
from events.processing import process_next, replay
from orders import services
from orders.models import Order

from .helpers import captured_body, post_event, queue_event

CHECKOUT = "/orders/api/checkout/"


def make_order(auth_client, product, shipping, qty=1):
    return auth_client.post(CHECKOUT, {**shipping, "items": [{"product_id": product.id, "quantity": qty}]}, format="json").data


def provider_id(order):
    return Order.objects.get(pk=order["id"]).provider_order_id


def test_captured_event_marks_order_paid(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    queue_event(provider_id(order), payment_id="pay_77")
    done = process_next()
    assert done.status == "DONE" and done.attempts == 1 and done.processed_at
    paid = Order.objects.get(pk=order["id"])
    assert (paid.status, paid.provider_payment_id) == ("PAID", "pay_77")


def test_full_flow_checkout_webhook_worker(auth_client, client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    assert post_event(client, captured_body(provider_id(order))).status_code == 200
    assert auth_client.get(f"/orders/api/orders/{order['id']}/").data["status"] == "PENDING"  # not yet processed
    call_command("process_events", "--once")
    assert auth_client.get(f"/orders/api/orders/{order['id']}/").data["status"] == "PAID"


def test_a_second_event_for_an_already_paid_order_is_harmless(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    queue_event(provider_id(order), event_id="evt_1", payment_id="pay_1")
    queue_event(provider_id(order), event_id="evt_2", payment_id="pay_1")
    assert process_next().status == "DONE" and process_next().status == "DONE"
    assert Order.objects.get(pk=order["id"]).status == "PAID"


def test_replaying_a_done_event_changes_nothing(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    event = queue_event(provider_id(order))
    process_next()
    replay([event.pk])
    assert process_next().status == "DONE"
    assert Order.objects.get(pk=order["id"]).status == "PAID"


def test_event_arriving_before_the_order_is_ready_is_retried_with_backoff(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    real_id = provider_id(order)
    Order.objects.filter(pk=order["id"]).update(provider_order_id="")  # webhook beat our own save
    queue_event(real_id)

    now = timezone.now()
    first = process_next(now=now)
    assert (first.status, first.attempts) == ("NEW", 1)
    assert first.next_run_at == now + timedelta(seconds=5) and "No order" in first.last_error
    assert process_next(now=now) is None                      # not due yet -> left alone

    Order.objects.filter(pk=order["id"]).update(provider_order_id=real_id)  # our save finally lands
    second = process_next(now=now + timedelta(seconds=6))
    assert (second.status, second.attempts, second.last_error) == ("DONE", 2, "")
    assert Order.objects.get(pk=order["id"]).status == "PAID"


def test_backoff_doubles_then_event_goes_dead_after_max_attempts():
    queue_event("order_that_never_exists")
    t = timezone.now()
    e = process_next(now=t)
    assert e.next_run_at == t + timedelta(seconds=5)
    t += timedelta(seconds=6)
    e = process_next(now=t)
    assert e.next_run_at == t + timedelta(seconds=10)
    t += timedelta(seconds=11)
    e = process_next(now=t)
    assert (e.status, e.attempts) == ("DEAD", 3) and "gave up after 3 attempts" in e.last_error
    assert process_next(now=t + timedelta(days=1)) is None    # dead events are never picked up again


def test_dead_event_can_be_replayed_after_the_cause_is_fixed(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    real_id = provider_id(order)
    Order.objects.filter(pk=order["id"]).update(provider_order_id="")
    event = queue_event(real_id, next_run_at=timezone.now() - timedelta(days=1))
    t = timezone.now()
    for _ in range(3):
        t += timedelta(minutes=1)
        process_next(now=t)
    event.refresh_from_db()
    assert event.status == "DEAD"

    Order.objects.filter(pk=order["id"]).update(provider_order_id=real_id)   # the human fixes the data
    assert replay([event.pk]) == 1
    event.refresh_from_db()
    assert (event.status, event.attempts, event.last_error) == ("NEW", 0, "")
    assert process_next().status == "DONE"
    assert Order.objects.get(pk=order["id"]).status == "PAID"


def test_payment_for_a_cancelled_order_goes_straight_to_dead_for_a_human_to_refund(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    auth_client.post(f"/orders/api/orders/{order['id']}/cancel/")
    queue_event(provider_id(order))
    e = process_next()
    assert (e.status, e.attempts) == ("DEAD", 1) and "refund needed" in e.last_error  # no pointless retries
    assert Order.objects.get(pk=order["id"]).status == "CANCELLED"


def test_payment_failed_event_leaves_the_order_pending(auth_client, phone, shipping):
    order = make_order(auth_client, phone, shipping)
    queue_event(provider_id(order), event_type="payment.failed")
    assert process_next().status == "DONE"
    assert Order.objects.get(pk=order["id"]).status == "PENDING"


def test_unknown_event_types_are_recorded_and_ignored():
    queue_event("x", event_type="refund.processed")
    assert process_next().status == "DONE"


def test_captured_event_without_payment_id_is_dead_not_retried():
    queue_event("mock_order_1", payment_id="")
    e = process_next()
    assert e.status == "DEAD" and e.attempts == 1


def test_oldest_due_event_goes_first_and_future_events_wait():
    now = timezone.now()
    later = queue_event("x", event_id="later", event_type="noop", next_run_at=now - timedelta(minutes=1))
    first = queue_event("x", event_id="first", event_type="noop", next_run_at=now - timedelta(minutes=5))
    queue_event("x", event_id="future", event_type="noop", next_run_at=now + timedelta(hours=1))
    assert process_next(now=now).pk == first.pk
    assert process_next(now=now).pk == later.pk
    assert process_next(now=now) is None


def test_worker_crash_mid_event_rolls_back_everything(auth_client, phone, shipping, monkeypatch):
    """If the process dies after the order was updated but before the event was marked done,
    BOTH changes vanish together - the event is simply waiting again."""
    order = make_order(auth_client, phone, shipping)
    event = queue_event(provider_id(order))

    def die_after_paying(ev):
        services.settle_payment(provider_order_id=ev.provider_order_id, payment_id=ev.payment_id)
        raise KeyboardInterrupt  # stands in for kill -9 / power loss: not caught by the worker's handlers

    monkeypatch.setattr(processing, "handle", die_after_paying)
    with pytest.raises(KeyboardInterrupt):
        process_next()

    event.refresh_from_db()
    assert (event.status, event.attempts) == ("NEW", 0)
    assert Order.objects.get(pk=order["id"]).status == "PENDING"

    monkeypatch.undo()
    assert process_next().status == "DONE"                    # a restarted worker finishes the job
    assert Order.objects.get(pk=order["id"]).status == "PAID"


def test_process_events_command_drains_the_queue(auth_client, phone, laptop, shipping):
    ids = [provider_id(make_order(auth_client, p, shipping)) for p in (phone, laptop)]
    for i, pid in enumerate(ids):
        queue_event(pid, event_id=f"evt_{i}")
    call_command("process_events", "--once")
    assert PaymentEvent.objects.filter(status="DONE").count() == 2
    assert Order.objects.filter(status="PAID").count() == 2
