import pytest

from .helpers import SECRET


@pytest.fixture(autouse=True)
def _webhook_settings(settings, db):
    settings.WEBHOOK_SECRET = SECRET
    settings.PAYMENT_PROVIDER = "mock"
    settings.EVENT_MAX_ATTEMPTS = 3
    settings.EVENT_BACKOFF_SECONDS = 5
