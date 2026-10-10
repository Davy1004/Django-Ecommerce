from products.models import Category, Product


def test_list_is_a_plain_array_with_category(client, phone, laptop):
    r = client.get("/api/products/")
    assert r.status_code == 200 and isinstance(r.data, list) and len(r.data) == 2
    assert r.data[0]["category"]["slug"] == "gadgets"
    assert isinstance(r.json()[0]["price"], (int, float))  # real JSON number, not a string


def test_filter_search_and_detail(client, phone, laptop):
    other = Category.objects.create(name="Books")
    Product.objects.create(category=other, name="Python Book", price="10", stock=1)
    assert len(client.get("/api/products/?category=books").data) == 1
    assert [p["name"] for p in client.get("/api/products/?search=lap").data] == ["Laptop"]
    assert client.get("/api/products/phone/").data["name"] == "Phone"
    assert client.get("/api/products/nope/").status_code == 404


def test_inactive_products_are_hidden(client, phone):
    phone.is_active = False
    phone.save()
    assert client.get("/api/products/").data == []
    assert client.get("/api/products/phone/").status_code == 404


def test_optional_pagination(client, phone, laptop):
    r = client.get("/api/products/?limit=1")
    assert r.data["count"] == 2 and len(r.data["results"]) == 1


def test_list_uses_constant_number_of_queries(client, category, django_assert_max_num_queries):
    for i in range(10):
        Product.objects.create(category=category, name=f"P{i}", price="1", stock=1)
    with django_assert_max_num_queries(2):  # not 1 + N
        client.get("/api/products/")


def test_category_detail_lists_products(client, phone):
    r = client.get("/api/categories/gadgets/")
    assert r.status_code == 200 and r.data["products"][0]["name"] == "Phone"


def test_health(client):
    assert client.get("/health/").json() == {"status": "ok"}
