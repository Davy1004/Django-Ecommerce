import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ("Create or update the dashboard admin from ADMIN_USERNAME / ADMIN_EMAIL / ADMIN_PASSWORD. "
            "Does nothing when they are not set, so no password ever lives in the repository. "
            "Hosting without a shell (Render free) runs this on every deploy instead of createsuperuser.")

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username or not password:
            self.stdout.write("ADMIN_USERNAME / ADMIN_PASSWORD not set - skipping admin user.")
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={"email": os.environ.get("ADMIN_EMAIL", "")})
        user.is_staff = user.is_superuser = True
        if os.environ.get("ADMIN_EMAIL"):
            user.email = os.environ["ADMIN_EMAIL"]
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Admin user {username!r} {'created' if created else 'updated'}."))
