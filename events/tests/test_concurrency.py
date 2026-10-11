"""Real-concurrency tests. They need PostgreSQL (SQLite has no row locks / SKIP LOCKED),
so they are skipped on SQLite. Run with:  DATABASE_URL=postgres://... pytest events/tests/test_concurrency.py
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connection, transaction
from rest_framework.test import APIClient

from events import processing
from events.models import PaymentEvent
from events.processing import process_next
from orders.models import Order

from .helpers import captured_body, post_event, queue_event

pytestmark = [
    pytest.mark.skipif(connection.vendor != "postgresql", reason="needs PostgreSQL row locking"),
    pytest.mark.django_db(transaction=True),
]


def in_thread(fn, timeout=10):
    """Run fn on its own database connection (its own transaction), like a separate worker process.
    Fails the test, instead of hanging it, if fn gets stuck waiting on a lock."""
    box = {}

    def run():
        try:
            box["value"] = fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller below
            box["error"] = exc
        finally:
            connection.close()

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        pytest.fail(f"worker blocked for more than {timeout}s on a locked row")
    if "error" in box:
        raise box["error"]
    return box["value"]


def make_paid_candidates(user, n):
    for i in range(n):
        Order.objects.create(user=user, provider_order_id=f"po_{i}", name="A", email="a@b.c",
                             address="x", city="y", phone="1", total_amount=10)
        queue_event(f"po_{i}", event_id=f"evt_{i}", payment_id=f"pay_{i}")


def test_many_workers_handle_every_event_exactly_once(user, monkeypatch):
    make_paid_candidates(user, 30)
    handled, guard = [], threading.Lock()
    real_handle = processing.handle

    def slow_handle(event):
        with guard:
            handled.append(event.pk)
        time.sleep(0.01)  # widen the window in which a second worker could grab the same row
        real_handle(event)
    monkeypatch.setattr(processing, "handle", slow_handle)

    def worker():
        try:
            while process_next() is not None:
                pass
        finally:
            connection.close()

    threads = [threading.Thread(target=worker) for _ in range(5)]
    [t.start() for t in threads]
    [t.join(timeout=60) for t in threads]

    assert len(handled) == 30 and len(set(handled)) == 30     # nobody handled an event twice
    assert PaymentEvent.objects.filter(status="DONE").count() == 30
    assert Order.objects.filter(status="PAID").count() == 30


def test_a_locked_event_is_skipped_not_waited_for(user):
    make_paid_candidates(user, 2)
    first, second = PaymentEvent.objects.order_by("id")
    with transaction.atomic():
        PaymentEvent.objects.select_for_update().get(pk=first.pk)   # "another worker" is busy with it
        started = time.monotonic()
        got = in_thread(process_next)                               # must not block behind that lock
        assert time.monotonic() - started < 5
    assert got.pk == second.pk
    first.refresh_from_db()
    assert first.status == "NEW"


def test_the_same_webhook_arriving_simultaneously_is_stored_once():
    body = captured_body("po_1", "evt_race")
    barrier = threading.Barrier(8)

    def deliver(_):
        try:
            barrier.wait(timeout=10)
            return post_event(APIClient(), body).data["status"]
        finally:
            connection.close()

    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(deliver, range(8)))
    assert sorted(results) == ["accepted"] + ["duplicate"] * 7
    assert PaymentEvent.objects.count() == 1
