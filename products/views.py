from django.db.models import Prefetch
from rest_framework import viewsets

from .models import Category, Product
from .serializers import (
    CategoryDetailSerializer,
    CategorySerializer,
    ProductSerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/products/?category=<slug>&search=<text>&ordering=price&limit=&offset="""

    serializer_class = ProductSerializer
    lookup_field = "slug"
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "created_at"]

    def get_queryset(self):
        # select_related -> one JOIN instead of one extra query per product (N+1)
        qs = Product.objects.filter(is_active=True).select_related("category")
        category = self.request.query_params.get("category")
        return qs.filter(category__slug=category) if category else qs


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        active = Product.objects.filter(is_active=True)
        return Category.objects.prefetch_related(Prefetch("products", queryset=active))

    def get_serializer_class(self):
        return CategoryDetailSerializer if self.action == "retrieve" else CategorySerializer
