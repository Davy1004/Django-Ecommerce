from rest_framework import serializers

from .models import Order, OrderItem


class CheckoutItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class CheckoutSerializer(serializers.Serializer):
    items = CheckoutItemSerializer(many=True, allow_empty=False, max_length=50)
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    address = serializers.CharField(max_length=1000)
    city = serializers.CharField(max_length=100)
    phone = serializers.RegexField(r"^\+?[0-9 \-]{7,20}$", error_messages={"invalid": "Enter a valid phone number."})

    SHIPPING_FIELDS = ("name", "email", "address", "city", "phone")

    def shipping(self):
        return {f: self.validated_data[f] for f in self.SHIPPING_FIELDS}


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product_id", "product_name", "unit_price", "quantity", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "total_amount", "name", "email", "address", "city", "phone",
                  "payment_provider", "created_at", "items"]


class PaySerializer(serializers.Serializer):
    payment_id = serializers.CharField(max_length=100)
    signature = serializers.CharField(max_length=256)
