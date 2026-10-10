from decimal import Decimal

from django.core.management.base import BaseCommand

from products.models import Category, Product

DEMO = {
    "Electronics": [("Wireless Earbuds", "1999.00", 40), ("Smart Watch", "4499.00", 25), ("Power Bank 20000mAh", "1599.00", 60)],
    "Books": [("Clean Code", "699.00", 30), ("Designing Data-Intensive Applications", "1299.00", 15)],
    "Home": [("Ceramic Mug Set", "499.00", 80), ("LED Desk Lamp", "899.00", 35)],
}


class Command(BaseCommand):
    help = "Create a few demo categories and products (safe to run more than once)."

    def handle(self, *args, **options):
        for cat_name, items in DEMO.items():
            category, _ = Category.objects.get_or_create(name=cat_name)
            for name, price, stock in items:
                Product.objects.get_or_create(
                    name=name,
                    defaults={"category": category, "price": Decimal(price), "stock": stock,
                              "description": f"{name} - demo product."},
                )
        self.stdout.write(self.style.SUCCESS("Demo catalogue ready."))
