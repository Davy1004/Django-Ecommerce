from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from events.models import PaymentEvent

from .helpers import queue_event

URL = "/events/status/"


def admin_client():
    get_user_model().objects.create_user("boss", "b@x.io", "pw-123456-x", is_staff=True)
    c = APIClient()
    token = c.post("/accounts/api/login/", {"username": "boss", "password": "pw-123456-x"}, format="json").data["access"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


def test_status_requires_admin(client, auth_client):
    assert client.get(URL).status_code == 401           # anonymous
    assert auth_client.get(URL).status_code == 403      # normal customer


def test_status_reports_counts_age_retries_and_dead_events():
    queue_event("o1", event_id="a")
    waiting = queue_event("o2", event_id="b", attempts=2)
    PaymentEvent.objects.filter(pk=waiting.pk).update(created_at=timezone.now() - timedelta(minutes=5))
    queue_event("o3", event_id="c", status="DONE")
    queue_event("o4", event_id="d", status="DEAD", last_error="refund needed", attempts=1)

    data = admin_client().get(URL).data
    assert data["counts"] == {"NEW": 2, "DONE": 1, "DEAD": 1}
    assert data["retrying"] == 1
    assert 290 <= data["oldest_waiting_age_seconds"] <= 330
    assert data["recent_dead"][0]["last_error"] == "refund needed"


def test_status_of_an_empty_queue():
    data = admin_client().get(URL).data
    assert data["counts"] == {"NEW": 0, "DONE": 0, "DEAD": 0}
    assert data["oldest_waiting_age_seconds"] is None and data["recent_dead"] == []
