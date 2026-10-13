from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Coupon
from products.models import Category, Product

# (name, price, stock, description). Slugs come from the name and must match the
# illustration file names in frontend/public/products/.
DEMO = {
    "Electronics": [
        ("Wireless Earbuds", "1999.00", 40, "True wireless earbuds with Bluetooth 5.3, 28-hour battery life with the charging case and a snug in-ear fit. Touch controls and a built-in mic make calls and playlists effortless."),
        ("Smart Watch", "4499.00", 25, "A 1.8-inch always-on display with heart-rate, sleep and step tracking, 100+ watch faces and 7-day battery life. Water resistant to 50 metres, so it keeps up with swims and rainy commutes."),
        ("Power Bank 20000mAh", "1599.00", 60, "Charge a phone four times over with this 20,000 mAh power bank. 22.5W fast charging, two USB-A ports, one USB-C and a four-light charge indicator."),
        ("Bluetooth Speaker", "2799.00", 30, "A portable speaker with deep bass and 360-degree sound. IPX6 water resistance, 12 hours of playtime and a pairing range of 10 metres."),
        ("Mechanical Keyboard", "3999.00", 20, "Hot-swappable tactile switches, PBT keycaps and per-key RGB lighting in a compact tenkeyless layout. Built to be typed on all day."),
        ("Laptop Stand", "1299.00", 45, "A foldable aluminium stand that lifts your screen to eye level and lets heat escape. Six height settings, non-slip pads, folds flat into a backpack."),
    ],
    "Books": [
        ("Clean Code", "699.00", 30, "Robert C. Martin's handbook of agile software craftsmanship. Learn to tell good code from bad, and how to turn bad code into good code."),
        ("Designing Data-Intensive Applications", "1299.00", 15, "Martin Kleppmann explains the ideas behind databases, replication, partitioning and streaming. The essential read for anyone building systems that must scale."),
        ("Introduction to Algorithms", "1899.00", 12, "The classic CLRS textbook: a rigorous and comprehensive tour of sorting, graphs, dynamic programming and more. Pairs well with interview preparation."),
        ("The Pragmatic Programmer", "899.00", 25, "Practical advice on becoming a better developer, from debugging and automation to thinking about your career. Short, readable chapters you can dip into."),
    ],
    "Home": [
        ("Ceramic Mug Set", "499.00", 80, "A set of two hand-glazed ceramic mugs in orange and blue. 350 ml each, microwave and dishwasher safe."),
        ("LED Desk Lamp", "899.00", 35, "A flexible-arm desk lamp with three colour temperatures and five brightness levels. Eye-care LEDs, touch control and a USB charging port."),
        ("Indoor Plant Pot", "349.00", 70, "A terracotta pot with a drainage hole and matching saucer, sized for herbs and small indoor plants. Plant not included."),
        ("Scented Candle", "399.00", 55, "A soy-wax candle poured in a reusable jar, scented with warm vanilla and sandalwood. Up to 40 hours of burn time."),
    ],
    "Fashion": [
        ("Canvas Backpack", "1499.00", 38, "A roomy 20-litre canvas backpack with a padded 15-inch laptop sleeve, a hidden back pocket and water-resistant lining."),
        ("Running Sneakers", "2499.00", 28, "Lightweight breathable mesh sneakers with a cushioned midsole and a grippy rubber outsole. Made for road runs and long days on your feet."),
        ("Aviator Sunglasses", "999.00", 50, "Classic metal-frame aviators with polarised, UV400 lenses. Comes with a hard case and a cleaning cloth."),
        ("Classic Cap", "399.00", 90, "A six-panel cotton cap with an adjustable strap and a curved brim. Soft, breathable, and goes with everything."),
    ],
    "Fitness": [
        ("Yoga Mat", "799.00", 42, "A 6 mm non-slip mat with a cushioned surface that is kind to your knees. Comes with a carry strap."),
        ("Hex Dumbbell Pair", "2999.00", 18, "A pair of rubber-coated hex dumbbells with knurled steel handles that will not roll away. Sold as a 5 kg pair."),
        ("Steel Water Bottle", "599.00", 75, "A 750 ml double-wall insulated bottle that keeps drinks cold for 24 hours or hot for 12. Leak-proof lid, BPA free."),
    ],
    "Stationery": [
        ("Hardcover Notebook", "249.00", 120, "A 192-page dotted notebook with 100 gsm paper that handles fountain pens, an elastic closure and a ribbon bookmark."),
        ("Fountain Pen", "649.00", 40, "A smooth-writing fountain pen with a fine steel nib and a weighted barrel. Includes a converter and two ink cartridges."),
        ("Desk Organiser", "549.00", 33, "A tidy three-compartment organiser for pens, notes and small gadgets. Sturdy, stackable and easy to wipe clean."),
    ],
}

COUPONS = [
    # code, description, kind, value, min order, max discount
    ("WELCOME10", "10% off your order (up to \u20b9500)", "PERCENT", "10", "0", "500"),
    ("FLAT200", "\u20b9200 off orders above \u20b91,500", "FIXED", "200", "1500", None),
    ("BOOKWORM15", "15% off, capped at \u20b9300", "PERCENT", "15", "500", "300"),
]


class Command(BaseCommand):
    help = "Create (or refresh) the demo catalogue. Safe to run on every deploy: stock and orders are never reset."

    def handle(self, *args, **options):
        for cat_name, items in DEMO.items():
            category, _ = Category.objects.get_or_create(name=cat_name)
            for name, price, stock, description in items:
                product, created = Product.objects.get_or_create(
                    name=name,
                    defaults={"category": category, "price": Decimal(price), "stock": stock, "description": description},
                )
                if not created:
                    # refresh the copy, but leave stock alone so a redeploy never undoes real sales
                    product.category, product.price, product.description = category, Decimal(price), description
                    product.save(update_fields=["category", "price", "description"])
        for code, description, kind, value, minimum, cap in COUPONS:
            Coupon.objects.update_or_create(code=code, defaults={
                "description": description, "kind": kind, "value": Decimal(value),
                "min_order_amount": Decimal(minimum), "max_discount": Decimal(cap) if cap else None,
            })  # used_count is not touched, so redeemed coupons stay redeemed across deploys
        self.stdout.write(self.style.SUCCESS(f"Demo catalogue ready: {Product.objects.count()} products."))
