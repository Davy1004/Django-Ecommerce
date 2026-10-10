import pytest


def test_register_returns_tokens_and_user(client):
    r = client.post("/accounts/api/register/", {"username": "ravi", "email": "r@example.com",
                    "password1": "long-enough-pw-1", "password2": "long-enough-pw-1"}, format="json")
    assert r.status_code == 201
    assert r.data["user"]["username"] == "ravi" and r.data["access"] and r.data["refresh"]


def test_register_rejects_mismatched_and_weak_passwords(client):
    r = client.post("/accounts/api/register/", {"username": "ravi", "email": "r@example.com",
                    "password1": "long-enough-pw-1", "password2": "different"}, format="json")
    assert r.status_code == 400 and "error" in r.data
    r = client.post("/accounts/api/register/", {"username": "ravi", "email": "r@example.com",
                    "password1": "12345678", "password2": "12345678"}, format="json")
    assert r.status_code == 400


def test_duplicate_username_rejected(client, user):
    r = client.post("/accounts/api/register/", {"username": "ASHA", "email": "x@example.com",
                    "password1": "long-enough-pw-1", "password2": "long-enough-pw-1"}, format="json")
    assert r.status_code == 400


def test_login_bad_password_is_401(client, user):
    r = client.post("/accounts/api/login/", {"username": "asha", "password": "nope"}, format="json")
    assert r.status_code == 401 and r.data["error"] == "Invalid credentials"


def test_me_requires_token_then_works(client, auth_client):
    assert client.get("/accounts/api/me/").status_code == 401
    r = auth_client.get("/accounts/api/me/")
    assert r.status_code == 200 and r.data["username"] == "asha"


def test_login_is_rate_limited(client, user):
    codes = [client.post("/accounts/api/login/", {"username": "asha", "password": "bad"}, format="json").status_code
             for _ in range(25)]
    assert 429 in codes
