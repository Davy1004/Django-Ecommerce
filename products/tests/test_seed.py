import pathlib

import pytest
from django.core.management import call_command

from products.models import Product

PUBLIC = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "public" / "products"


@pytest.mark.django_db
def test_seed_is_idempotent_and_keeps_stock():
    call_command("seed_demo")
    n = Product.objects.count()
    p = Product.objects.get(slug="clean-code")
    Product.objects.filter(pk=p.pk).update(stock=3, description="old copy")
    call_command("seed_demo")
    p.refresh_from_db()
    assert Product.objects.count() == n
    assert p.stock == 3  # a redeploy never resets stock
    assert p.description != "old copy"  # but the copy is refreshed


@pytest.mark.django_db
def test_every_product_has_an_illustration():
    call_command("seed_demo")
    missing = [p.slug for p in Product.objects.all() if not (PUBLIC / f"{p.slug}.svg").exists()]
    assert not missing
