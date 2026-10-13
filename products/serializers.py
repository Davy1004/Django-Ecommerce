from rest_framework import serializers

from .models import Category, Product, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    image = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "price", "stock", "description", "image", "category", "avg_rating", "review_count"]

    # Filled by ProductViewSet's annotate(); other callers just get "no ratings yet".
    def get_avg_rating(self, obj):
        value = getattr(obj, "avg_rating", None)
        return round(value, 1) if value is not None else None

    def get_review_count(self, obj):
        return getattr(obj, "review_count", 0) or 0

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class ProductBriefSerializer(ProductSerializer):
    class Meta(ProductSerializer.Meta):
        fields = ["id", "name", "slug", "price", "stock", "image"]


class CategoryDetailSerializer(CategorySerializer):
    products = ProductBriefSerializer(many=True, read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ["products"]


class ReviewInputSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    body = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="user.username", read_only=True)
    verified_purchase = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "rating", "title", "body", "author", "verified_purchase", "is_mine", "created_at"]

    def get_verified_purchase(self, obj):
        return obj.user_id in self.context.get("verified_user_ids", ())

    def get_is_mine(self, obj):
        user = self.context["request"].user
        return bool(user.is_authenticated and obj.user_id == user.id)
