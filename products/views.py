from django.db.models import Avg, Count, F, Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Review, WishlistItem
from .serializers import (
    CategoryDetailSerializer,
    CategorySerializer,
    ProductSerializer,
    ReviewInputSerializer,
    ReviewSerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/products/?category=<slug>&search=<text>&ordering=price&limit=&offset="""

    serializer_class = ProductSerializer
    lookup_field = "slug"
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "created_at"]

    def get_throttles(self):
        # only writes to reviews are rate limited; browsing stays unthrottled
        if getattr(self, "action", None) == "reviews" and self.request.method in ("POST", "DELETE"):
            self.throttle_scope = "review"
        return super().get_throttles()

    def get_queryset(self):
        # select_related -> one JOIN instead of one extra query per product (N+1);
        # annotate -> average rating and review count come from the same query
        qs = (Product.objects.filter(is_active=True).select_related("category")
              .annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews")))
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        if self.request.query_params.get("ordering") == "rating":  # best rated first, unrated last
            qs = qs.order_by(F("avg_rating").desc(nulls_last=True), "-review_count", "id")
        return qs

    @action(detail=True, methods=["get", "post", "delete"], url_path="reviews")
    def reviews(self, request, slug=None):
        """GET: summary + reviews. POST {rating, title?, body?}: add or update YOUR review. DELETE: remove it."""
        product = self.get_object()
        if request.method == "GET":
            return Response(review_payload(product, request))
        if not request.user.is_authenticated:
            return Response({"error": "Sign in to review products."}, status=status.HTTP_401_UNAUTHORIZED)
        if request.method == "DELETE":
            deleted, _ = Review.objects.filter(product=product, user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT if deleted else status.HTTP_404_NOT_FOUND)
        data = ReviewInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        _, created = Review.objects.update_or_create(product=product, user=request.user, defaults=data.validated_data)
        return Response(review_payload(product, request), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


def review_payload(product, request):
    from orders.models import Order, OrderItem

    reviews = list(product.reviews.select_related("user")[:100])
    buyers = set(OrderItem.objects.filter(
        product=product, order__status=Order.Status.PAID, order__user_id__in=[r.user_id for r in reviews],
    ).values_list("order__user_id", flat=True))
    stats = product.reviews.aggregate(average=Avg("rating"), count=Count("id"))
    dist = {str(i): 0 for i in range(1, 6)}
    for row in product.reviews.values("rating").annotate(n=Count("id")):
        dist[str(row["rating"])] = row["n"]
    return {
        "summary": {"average": round(stats["average"], 1) if stats["average"] is not None else None,
                    "count": stats["count"], "distribution": dist},
        "results": ReviewSerializer(reviews, many=True, context={"request": request, "verified_user_ids": buyers}).data,
    }


class WishlistView(APIView):
    """GET /api/wishlist/ -> your saved products. POST {product_id} saves one (idempotent)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = list(WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True))
        products = {p.id: p for p in Product.objects.filter(id__in=ids, is_active=True).select_related("category")
                    .annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews"))}
        results = [ProductSerializer(products[i], context={"request": request}).data for i in ids if i in products]
        return Response({"count": len(results), "results": results})

    def post(self, request):
        try:
            product_id = int(request.data.get("product_id"))
        except (TypeError, ValueError):
            return Response({"error": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not Product.objects.filter(pk=product_id, is_active=True).exists():
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        _, created = WishlistItem.objects.get_or_create(user=request.user, product_id=product_id)
        return Response({"product_id": product_id}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class WishlistItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()  # removing twice is fine
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        active = Product.objects.filter(is_active=True)
        return Category.objects.prefetch_related(Prefetch("products", queryset=active))

    def get_serializer_class(self):
        return CategoryDetailSerializer if self.action == "retrieve" else CategorySerializer
