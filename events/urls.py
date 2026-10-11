from django.urls import path

from . import views

urlpatterns = [
    path("webhook/", views.PaymentWebhookView.as_view(), name="payment_webhook"),
]
