import pytest


VALID_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def test_register_success(client):
    r = client.post("/v1/auth/register", json=VALID_USER)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == VALID_USER["username"]
    assert data["email"] == VALID_USER["email"]
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_username(client):
    client.post("/v1/auth/register", json=VALID_USER)
    r = client.post("/v1/auth/register", json={**VALID_USER, "email": "other@example.com"})
    assert r.status_code == 409
    assert "username" in r.json()["detail"].lower()


def test_register_duplicate_email(client):
    client.post("/v1/auth/register", json=VALID_USER)
    r = client.post("/v1/auth/register", json={**VALID_USER, "username": "other"})
    assert r.status_code == 409
    assert "email" in r.json()["detail"].lower()


def test_register_password_too_short(client):
    r = client.post("/v1/auth/register", json={**VALID_USER, "password": "short"})
    assert r.status_code == 422


def test_register_invalid_email(client):
    r = client.post("/v1/auth/register", json={**VALID_USER, "email": "not-an-email"})
    assert r.status_code == 422


def test_register_password_no_digit(client):
    r = client.post("/v1/auth/register", json={**VALID_USER, "password": "abcdefgh"})
    assert r.status_code == 422


def test_register_password_no_letter(client):
    r = client.post("/v1/auth/register", json={**VALID_USER, "password": "12345678"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_success(client):
    client.post("/v1/auth/register", json=VALID_USER)
    r = client.post("/v1/auth/login", data={
        "username": VALID_USER["username"],
        "password": VALID_USER["password"],
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/v1/auth/register", json=VALID_USER)
    r = client.post("/v1/auth/login", data={
        "username": VALID_USER["username"],
        "password": "wrongpassword",
    })
    assert r.status_code == 401


def test_login_nonexistent_user(client):
    r = client.post("/v1/auth/login", data={
        "username": "nobody",
        "password": "password123",
    })
    assert r.status_code == 401
