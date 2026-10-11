import time

from django.core.management.base import BaseCommand

from events.processing import process_next


class Command(BaseCommand):
    help = ("Worker: handle queued payment events. Without --once it runs forever (polling); "
            "with --once it handles everything that is due, then exits (good for a scheduler).")

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="drain the due events and exit")
        parser.add_argument("--sleep", type=float, default=2.0, help="seconds to wait when the queue is empty")

    def handle(self, *args, **options):
        self.stdout.write("Worker started. Ctrl+C to stop.")
        try:
            while True:
                event = process_next()
                if event is not None:
                    self.stdout.write(f"event {event.event_id} ({event.event_type}) -> {event.status}"
                                      f" (attempt {event.attempts})" + (f": {event.last_error}" if event.last_error else ""))
                    continue
                if options["once"]:
                    break
                time.sleep(options["sleep"])
        except KeyboardInterrupt:
            self.stdout.write("Worker stopped.")
