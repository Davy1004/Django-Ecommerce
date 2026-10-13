from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("api/admin/sales/", views.SalesDashboardView.as_view(), name="sales_dashboard"),
]
