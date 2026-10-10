from django.db import connection
from django.http import JsonResponse


def health(request):
    """Used by the hosting platform to know the app (and its database) is alive."""
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
    return JsonResponse({"status": "ok"})
