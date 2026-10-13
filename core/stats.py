"""Numbers for the admin dashboard. Revenue always means PAID orders only: pending and
cancelled orders are shown as counts but never as money earned."""
from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from orders.models import Coupon, Order, OrderItem
from products.models import Product, Review

ZERO = Decimal("0")
LOW_STOCK = 5


def _money(value):
    return float(value or ZERO)


def sales_dashboard(days=30, now=None):
    tz = ZoneInfo(settings.STATS_TIMEZONE)
    now = now or timezone.now()
    today = now.astimezone(tz).date()
    start_day = today - timedelta(days=days - 1)
    start = timezone.make_aware(timezone.datetime.combine(start_day, timezone.datetime.min.time()), tz)

    paid = Order.objects.filter(status=Order.Status.PAID)
    paid_in_range = paid.filter(created_at__gte=start)

    # --- headline numbers (whole history) ---
    totals = paid.aggregate(revenue=Sum("total_amount"), orders=Count("id"), discount=Sum("discount_amount"), aov=Avg("total_amount"))
    by_status = {s: 0 for s in Order.Status.values}
    for row in Order.objects.values("status").annotate(n=Count("id")):
        by_status[row["status"]] = row["n"]
    units = OrderItem.objects.filter(order__status=Order.Status.PAID).aggregate(n=Sum("quantity"))["n"] or 0
    customers = paid.values("user").distinct().count()

    # --- range numbers + zero-filled daily series ---
    range_totals = paid_in_range.aggregate(revenue=Sum("total_amount"), orders=Count("id"))
    daily = {
        row["day"]: row for row in paid_in_range.annotate(day=TruncDate("created_at", tzinfo=tz))
        .values("day").annotate(revenue=Sum("total_amount"), orders=Count("id"))
    }
    series = []
    for i in range(days):
        day = start_day + timedelta(days=i)
        row = daily.get(day)
        series.append({"date": day.isoformat(), "revenue": _money(row and row["revenue"]), "orders": row["orders"] if row else 0})

    # --- breakdowns (paid orders in range) ---
    line_revenue = ExpressionWrapper(F("unit_price") * F("quantity"), output_field=DecimalField(max_digits=14, decimal_places=2))
    lines = OrderItem.objects.filter(order__in=paid_in_range)
    top_products = [
        {"name": r["product_name"], "units": r["units"], "revenue": _money(r["revenue"])}
        for r in lines.values("product_name").annotate(units=Sum("quantity"), revenue=Sum(line_revenue)).order_by("-revenue")[:6]
    ]
    by_category = [
        {"category": r["product__category__name"], "units": r["units"], "revenue": _money(r["revenue"])}
        for r in lines.values("product__category__name").annotate(units=Sum("quantity"), revenue=Sum(line_revenue)).order_by("-revenue")
    ]
    coupons = [
        {"code": r["coupon_code"], "orders": r["orders"], "discount": _money(r["discount"])}
        for r in paid_in_range.exclude(coupon_code="").values("coupon_code")
        .annotate(orders=Count("id"), discount=Sum("discount_amount")).order_by("-orders")[:5]
    ]

    low_stock = list(Product.objects.filter(is_active=True, stock__lte=LOW_STOCK).order_by("stock", "name")
                     .values("id", "name", "slug", "stock")[:8])
    recent = [
        {"id": o.id, "customer": o.user.username, "status": o.status, "total": _money(o.total_amount), "created_at": o.created_at.isoformat()}
        for o in Order.objects.select_related("user").order_by("-created_at", "-id")[:8]
    ]
    reviews = Review.objects.aggregate(n=Count("id"), avg=Avg("rating"))

    return {
        "days": days,
        "totals": {
            "revenue": _money(totals["revenue"]), "paid_orders": totals["orders"], "units_sold": units,
            "average_order_value": _money(totals["aov"]), "discounts_given": _money(totals["discount"]),
            "customers": customers, "orders_by_status": by_status,
        },
        "range": {"revenue": _money(range_totals["revenue"]), "orders": range_totals["orders"]},
        "daily": series,
        "top_products": top_products,
        "by_category": by_category,
        "coupons": coupons,
        "low_stock": low_stock,
        "recent_orders": recent,
        "catalogue": {"products": Product.objects.filter(is_active=True).count(), "coupons_active": Coupon.objects.filter(is_active=True).count(),
                      "reviews": reviews["n"], "average_rating": round(reviews["avg"], 1) if reviews["avg"] else None},
    }
