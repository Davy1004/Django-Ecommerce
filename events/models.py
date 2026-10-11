from django.db import models
from django.db.models import Q
from django.utils import timezone


class PaymentEvent(models.Model):
    """One webhook from the payment provider. The table IS the queue.

    NEW  -> waiting (or waiting for its retry time)
    DONE -> processed (or deliberately ignored)
    DEAD -> gave up; a human looks at last_error, fixes the cause and replays it from the admin
    """

    class Status(models.TextChoices):
        NEW = "NEW", "Waiting"
        DONE = "DONE", "Done"
        DEAD = "DEAD", "Dead (needs a human)"

    provider = models.CharField(max_length=20)
    event_id = models.CharField(max_length=100)  # the provider's own id for this event
    event_type = models.CharField(max_length=50)
    provider_order_id = models.CharField(max_length=100, blank=True)
    payment_id = models.CharField(max_length=100, blank=True)
    payload = models.JSONField()  # raw body, kept for debugging and replay

    status = models.CharField(max_length=8, choices=Status.choices, default=Status.NEW)
    attempts = models.PositiveIntegerField(default=0)
    next_run_at = models.DateTimeField(default=timezone.now)  # retry/backoff schedule
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            # The providers retry webhooks, so the same event WILL arrive twice.
            # The database - not application code - guarantees we store it once.
            models.UniqueConstraint(fields=["provider", "event_id"], name="uniq_event_per_provider"),
        ]
        indexes = [
            # Tiny index containing only the rows a worker cares about.
            models.Index(fields=["next_run_at"], condition=Q(status="NEW"), name="event_queue_idx"),
        ]

    def __str__(self):
        return f"{self.event_type} {self.event_id} [{self.status}]"
