import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from products.models import Category, Product


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()  # throttling counters live in the cache
    yield


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user("asha", "asha@example.com", "s3cret-pass-99")


@pytest.fixture
def client(db):
    return APIClient()


@pytest.fixture
def auth_client(user):
    c = APIClient()
    resp = c.post("/accounts/api/login/", {"username": "asha", "password": "s3cret-pass-99"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return c


@pytest.fixture
def category(db):
    return Category.objects.create(name="Gadgets")


@pytest.fixture
def phone(category):
    return Product.objects.create(category=category, name="Phone", price="100.00", stock=5)


@pytest.fixture
def laptop(category):
    return Product.objects.create(category=category, name="Laptop", price="250.50", stock=2)


SHIPPING = {"name": "Asha", "email": "asha@example.com", "address": "1 Main St", "city": "Pune", "phone": "+91 98765 43210"}


@pytest.fixture
def shipping():
    return dict(SHIPPING)
