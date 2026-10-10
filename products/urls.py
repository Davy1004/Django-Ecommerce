from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register("api/products", ProductViewSet, basename="product")
router.register("api/categories", CategoryViewSet, basename="category")

urlpatterns = router.urls
