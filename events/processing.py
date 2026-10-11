"""The worker's brain: claim one event, handle it, record the outcome.

How a worker claims work safely
  SELECT ... FOR UPDATE SKIP LOCKED  = "give me the next waiting row that nobody else has
  locked; if another worker is holding it, skip it instead of waiting".
So any number of workers can run at once and no event is handled twice at the same time.

Crash safety
  The claim, the handling and the result are ONE transaction. If the worker dies half-way,
  Postgres rolls everything back and releases the lock: the event is simply NEW again.
  That is why there is no "PROCESSING" status to get stuck in.

Delivery is "at least once" (a crash can cause a retry), so handlers must be idempotent.
Ours are: paying an already-paid order does nothing.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from orders.services import OrderNotFound, OrderNotPayable, settle_payment

from .models import PaymentEvent

log = logging.getLogger("events")


class RetryableError(Exception):
    """Might work later (e.g. the webhook arrived before our order was fully saved)."""


class PermanentError(Exception):
    """Will never work by retrying; send straight to the dead-letter state."""


def handle(event):
    if event.event_type == "payment.captured":
        if not event.provider_order_id or not event.payment_id:
            raise PermanentError("payment.captured without order id / payment id")
        try:
            settle_payment(provider_order_id=event.provider_order_id, payment_id=event.payment_id)
        except OrderNotFound as exc:
            raise RetryableError(str(exc)) from exc   # out-of-order delivery: try again shortly
        except OrderNotPayable as exc:
            raise PermanentError(str(exc)) from exc   # money taken for a cancelled order: human must refund
    # payment.failed: the order stays PENDING so the customer can try again (or it expires).
    # Any other event type is stored for the record and deliberately ignored.


def backoff_delay(attempts):
    return timedelta(seconds=settings.EVENT_BACKOFF_SECONDS * 2 ** (attempts - 1))  # 5s, 10s, 20s...


def process_next(now=None):
    """Handle at most one due event. Returns it, or None when the queue has nothing due."""
    now = now or timezone.now()
    with transaction.atomic():
        event = (PaymentEvent.objects.select_for_update(skip_locked=True)
                 .filter(status=PaymentEvent.Status.NEW, next_run_at__lte=now)
                 .order_by("next_run_at", "id").first())
        if event is None:
            return None
        event.attempts += 1
        try:
            with transaction.atomic():  # savepoint: a failed handler must not leave half-writes
                handle(event)
        except PermanentError as exc:
            _give_up(event, str(exc), now)
        except Exception as exc:  # noqa: BLE001 - any failure is retried, then dead-lettered
            if event.attempts >= settings.EVENT_MAX_ATTEMPTS:
                _give_up(event, f"gave up after {event.attempts} attempts: {exc}", now)
            else:
                event.last_error = str(exc)
                event.next_run_at = now + backoff_delay(event.attempts)
                log.warning("event %s failed (attempt %s), retrying: %s", event.event_id, event.attempts, exc)
        else:
            event.status = PaymentEvent.Status.DONE
            event.processed_at = now
            event.last_error = ""
        event.save()
    return event


def _give_up(event, reason, now):
    event.status = PaymentEvent.Status.DEAD
    event.last_error = reason
    event.processed_at = now
    log.error("event %s is DEAD: %s", event.event_id, reason)


def replay(event_ids):
    """Put dead (or any) events back in the queue, e.g. after fixing the cause. Returns the count."""
    return PaymentEvent.objects.filter(pk__in=event_ids).update(
        status=PaymentEvent.Status.NEW, attempts=0, next_run_at=timezone.now(),
        last_error="", processed_at=None)
