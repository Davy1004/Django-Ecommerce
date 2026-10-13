from django.db import connection
from django.http import JsonResponse
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .stats import sales_dashboard


def health(request):
    """Used by the hosting platform to know the app (and its database) is alive."""
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


class SalesDashboardView(APIView):
    """GET /api/admin/sales/?days=30 - staff only. Everything the dashboard page shows, in one call."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            days = min(max(int(request.query_params.get("days", 30)), 1), 365)
        except ValueError:
            days = 30
        return Response(sales_dashboard(days))
