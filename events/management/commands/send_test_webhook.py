import json
import urllib.error
import urllib.request
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from events.parsing import sign
from orders.models import Order


class Command(BaseCommand):
    help = ("Demo helper: pretend to be the payment provider and POST a signed 'payment.captured' "
            "webhook for an order. Use --times 2 to see duplicate delivery being ignored.")

    def add_arguments(self, parser):
        parser.add_argument("order_id", type=int)
        parser.add_argument("--url", default="http://localhost:8000/events/webhook/")
        parser.add_argument("--times", type=int, default=1)
        parser.add_argument("--event-type", default="payment.captured")

    def handle(self, *args, **options):
        if settings.PAYMENT_PROVIDER != "mock":
            raise CommandError("This helper only builds mock-provider events.")
        if not settings.WEBHOOK_SECRET:
            raise CommandError("Set WEBHOOK_SECRET first (same value for the server and this command).")
        order = Order.objects.filter(pk=options["order_id"]).first()
        if not order or not order.provider_order_id:
            raise CommandError("Order not found, or it has no provider order id.")

        body = json.dumps({"id": f"evt_{uuid.uuid4().hex[:12]}", "type": options["event_type"],
                           "order_id": order.provider_order_id,
                           "payment_id": f"pay_{uuid.uuid4().hex[:10]}"}).encode()
        headers = {"Content-Type": "application/json", "X-Webhook-Signature": sign(body, settings.WEBHOOK_SECRET)}
        for i in range(options["times"]):  # same body each time = same event id = a duplicate delivery
            req = urllib.request.Request(options["url"], data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    self.stdout.write(f"#{i + 1}: {resp.status} {resp.read().decode()}")
            except urllib.error.HTTPError as exc:
                self.stdout.write(f"#{i + 1}: {exc.code} {exc.read().decode()}")
