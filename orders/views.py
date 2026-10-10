from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Order
from .payments import get_provider
from .serializers import CheckoutSerializer, OrderSerializer, PaySerializer


def checkout_error(exc):
    body = {"error": exc.message}
    if exc.details is not None:
        body["details"] = exc.details
    return Response(body, status=exc.status_code)


class CheckoutView(APIView):
    """POST /orders/api/checkout/

    Body: {items: [{product_id, quantity}], name, email, address, city, phone}
    Optional header: Idempotency-Key (any unique string per attempt).
    """

    permission_classes = [IsAuthenticated]
    throttle_scope = "checkout"

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = (request.headers.get("Idempotency-Key") or "").strip()[:64] or None
        try:
            order, created = services.place_order(
                user=request.user,
                items=serializer.validated_data["items"],
                shipping=serializer.shipping(),
                idempotency_key=key,
            )
        except services.CheckoutError as exc:
            return checkout_error(exc)
        data = OrderSerializer(order).data
        data["payment"] = get_provider().public_info(order)
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class MyOrdersMixin:
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items")


class OrderListView(MyOrdersMixin, generics.ListAPIView):
    serializer_class = OrderSerializer


class OrderDetailView(MyOrdersMixin, generics.RetrieveAPIView):
    serializer_class = OrderSerializer


class PayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = PaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = services.confirm_payment(order_id=pk, user=request.user, **serializer.validated_data)
        except services.CheckoutError as exc:
            return checkout_error(exc)
        return Response(OrderSerializer(order).data)


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = generics.get_object_or_404(Order, pk=pk, user=request.user)
        try:
            order = services.cancel_order(order)
        except services.CheckoutError as exc:
            return checkout_error(exc)
        return Response(OrderSerializer(order).data)
