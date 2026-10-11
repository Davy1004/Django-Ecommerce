from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentEvent
from .parsing import WebhookRejected, parse_webhook


class PaymentWebhookView(APIView):
    """Receive -> verify -> store -> answer fast. NO business logic here.

    Providers give up (or retry harder) if we are slow, so the real work happens later in the
    worker. Duplicates still get a 2xx: "we already have it" must not make the provider retry.
    """

    authentication_classes = []   # the signature is the authentication
    permission_classes = [AllowAny]
    throttle_classes = []         # providers send bursts; the signature already filters abuse

    def post(self, request):
        try:
            event = parse_webhook(request.headers, request.body)
        except WebhookRejected as exc:
            return Response({"detail": str(exc)}, status=exc.status_code)

        try:
            with transaction.atomic():  # savepoint, so a duplicate doesn't poison an outer transaction
                PaymentEvent.objects.create(
                    provider=event.provider, event_id=event.event_id, event_type=event.event_type,
                    provider_order_id=event.provider_order_id, payment_id=event.payment_id,
                    payload=event.payload,
                )
        except IntegrityError:
            return Response({"status": "duplicate"})
        return Response({"status": "accepted"})


class QueueStatusView(APIView):
    """Admin-only health view of the pipeline: how many events per state, how stale the oldest
    waiting one is, and the latest dead ones. This is what you would alert on in production."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        counts = {s: 0 for s in PaymentEvent.Status.values}
        for row in PaymentEvent.objects.values("status").annotate(n=Count("id")):
            counts[row["status"]] = row["n"]

        waiting = PaymentEvent.objects.filter(status=PaymentEvent.Status.NEW)
        oldest = waiting.order_by("created_at").values_list("created_at", flat=True).first()
        dead = PaymentEvent.objects.filter(status=PaymentEvent.Status.DEAD).order_by("-id")[:10]
        return Response({
            "counts": counts,
            "oldest_waiting_age_seconds": int((timezone.now() - oldest).total_seconds()) if oldest else None,
            "retrying": waiting.filter(attempts__gt=0).count(),
            "recent_dead": [
                {"id": e.id, "event_type": e.event_type, "provider_order_id": e.provider_order_id,
                 "attempts": e.attempts, "last_error": e.last_error} for e in dead
            ],
        })
