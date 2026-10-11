from django.db import IntegrityError, transaction
from rest_framework.permissions import AllowAny
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
