from django.core.management.base import BaseCommand

from orders.services import expire_pending_orders


class Command(BaseCommand):
    help = "Cancel unpaid orders older than PENDING_ORDER_TTL_MINUTES and release their stock. Run on a schedule."

    def handle(self, *args, **options):
        n = expire_pending_orders()
        self.stdout.write(self.style.SUCCESS(f"Cancelled {n} expired order(s)."))
