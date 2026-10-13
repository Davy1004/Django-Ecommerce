from django.urls import path

from . import views

urlpatterns = [
    path("api/checkout/", views.CheckoutView.as_view(), name="checkout_api"),
    path("api/coupons/validate/", views.CouponPreviewView.as_view(), name="coupon_validate"),
    path("api/orders/", views.OrderListView.as_view(), name="order_list"),
    path("api/orders/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("api/orders/<int:pk>/pay/", views.PayOrderView.as_view(), name="order_pay"),
    path("api/orders/<int:pk>/cancel/", views.CancelOrderView.as_view(), name="order_cancel"),
]
