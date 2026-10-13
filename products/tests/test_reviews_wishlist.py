import pytest
from rest_framework.test import APIClient

from products.models import Product, Review, WishlistItem

CHECKOUT = "/orders/api/checkout/"


def reviews_url(p):
    return f"/api/products/{p.slug}/reviews/"


@pytest.fixture
def second_client(django_user_model):
    django_user_model.objects.create_user("bo", "bo@example.com", "s3cret-pass-99")
    c = APIClient()
    tok = c.post("/accounts/api/login/", {"username": "bo", "password": "s3cret-pass-99"}, format="json").data["access"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}")
    return c


# ---------- reviews ----------
def test_anyone_can_read_reviews_but_must_sign_in_to_write(client, phone):
    r = client.get(reviews_url(phone))
    assert r.status_code == 200 and r.data["summary"] == {"average": None, "count": 0, "distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}}
    assert client.post(reviews_url(phone), {"rating": 5}, format="json").status_code == 401


def test_post_creates_then_updates_one_review_per_user(auth_client, phone):
    a = auth_client.post(reviews_url(phone), {"rating": 4, "title": "Good", "body": "Works"}, format="json")
    assert a.status_code == 201 and a.data["summary"]["count"] == 1
    b = auth_client.post(reviews_url(phone), {"rating": 2, "title": "Changed my mind"}, format="json")
    assert b.status_code == 200 and b.data["summary"]["count"] == 1 and b.data["summary"]["average"] == 2.0
    assert Review.objects.count() == 1
    mine = b.data["results"][0]
    assert mine["is_mine"] is True and mine["author"] == "asha" and mine["title"] == "Changed my mind"


@pytest.mark.parametrize("bad", [{}, {"rating": 0}, {"rating": 6}, {"rating": "x"}, {"rating": 3, "title": "x" * 121}])
def test_validation(auth_client, phone, bad):
    assert auth_client.post(reviews_url(phone), bad, format="json").status_code == 400
    assert Review.objects.count() == 0


def test_average_distribution_and_delete(auth_client, second_client, phone):
    auth_client.post(reviews_url(phone), {"rating": 5}, format="json")
    r = second_client.post(reviews_url(phone), {"rating": 2}, format="json")
    assert r.data["summary"] == {"average": 3.5, "count": 2, "distribution": {"1": 0, "2": 1, "3": 0, "4": 0, "5": 1}}
    assert {x["is_mine"] for x in r.data["results"]} == {True, False}
    assert second_client.delete(reviews_url(phone)).status_code == 204
    assert second_client.delete(reviews_url(phone)).status_code == 404
    assert Review.objects.count() == 1  # only bo's was removed


def test_verified_purchase_badge_only_after_payment(auth_client, second_client, phone, shipping):
    oid = auth_client.post(CHECKOUT, {**shipping, "items": [{"product_id": phone.id, "quantity": 1}]}, format="json").data["id"]
    auth_client.post(reviews_url(phone), {"rating": 5}, format="json")
    second_client.post(reviews_url(phone), {"rating": 4}, format="json")
    def flags():
        return {x["author"]: x["verified_purchase"] for x in auth_client.get(reviews_url(phone)).data["results"]}
    assert flags() == {"asha": False, "bo": False}  # unpaid order does not count
    auth_client.post(f"/orders/api/orders/{oid}/pay/", {"payment_id": "p", "signature": "mock_success"}, format="json")
    assert flags() == {"asha": True, "bo": False}


def test_products_expose_rating_and_can_sort_by_it(client, auth_client, phone, laptop):
    auth_client.post(reviews_url(laptop), {"rating": 5}, format="json")
    data = client.get("/api/products/").data
    by = {p["slug"]: p for p in data}
    assert by["laptop"]["avg_rating"] == 5.0 and by["laptop"]["review_count"] == 1
    assert by["phone"]["avg_rating"] is None and by["phone"]["review_count"] == 0
    assert [p["slug"] for p in client.get("/api/products/?ordering=rating").data] == ["laptop", "phone"]
    assert client.get("/api/products/laptop/").data["avg_rating"] == 5.0


def test_rating_list_uses_constant_queries(client, django_assert_max_num_queries, phone, laptop):
    with django_assert_max_num_queries(3):
        client.get("/api/products/")


# ---------- wishlist ----------
def test_wishlist_requires_login(client, phone):
    assert client.get("/api/wishlist/").status_code == 401
    assert client.post("/api/wishlist/", {"product_id": phone.id}, format="json").status_code == 401


def test_wishlist_add_list_remove(auth_client, phone, laptop):
    assert auth_client.post("/api/wishlist/", {"product_id": phone.id}, format="json").status_code == 201
    assert auth_client.post("/api/wishlist/", {"product_id": phone.id}, format="json").status_code == 200  # idempotent
    auth_client.post("/api/wishlist/", {"product_id": laptop.id}, format="json")
    r = auth_client.get("/api/wishlist/")
    assert r.data["count"] == 2 and [p["slug"] for p in r.data["results"]] == ["laptop", "phone"]  # newest first
    assert auth_client.delete(f"/api/wishlist/{phone.id}/").status_code == 204
    assert auth_client.delete(f"/api/wishlist/{phone.id}/").status_code == 204
    assert [p["slug"] for p in auth_client.get("/api/wishlist/").data["results"]] == ["laptop"]


def test_wishlist_is_private_and_validates(auth_client, second_client, phone):
    auth_client.post("/api/wishlist/", {"product_id": phone.id}, format="json")
    assert second_client.get("/api/wishlist/").data["count"] == 0
    assert second_client.delete(f"/api/wishlist/{phone.id}/").status_code == 204
    assert WishlistItem.objects.count() == 1  # bo cannot remove asha's item
    assert auth_client.post("/api/wishlist/", {"product_id": 99999}, format="json").status_code == 404
    assert auth_client.post("/api/wishlist/", {}, format="json").status_code == 400


def test_inactive_products_drop_out_of_wishlist(auth_client, phone):
    auth_client.post("/api/wishlist/", {"product_id": phone.id}, format="json")
    Product.objects.filter(pk=phone.pk).update(is_active=False)
    assert auth_client.get("/api/wishlist/").data["count"] == 0
