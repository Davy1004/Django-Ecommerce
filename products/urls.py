from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet, WishlistItemView, WishlistView

router = DefaultRouter()
router.register("api/products", ProductViewSet, basename="product")
router.register("api/categories", CategoryViewSet, basename="category")

urlpatterns = [
    path("api/wishlist/", WishlistView.as_view(), name="wishlist"),
    path("api/wishlist/<int:product_id>/", WishlistItemView.as_view(), name="wishlist_item"),
] + router.urls
