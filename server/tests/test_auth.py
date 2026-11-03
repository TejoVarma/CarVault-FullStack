import pytest

from tests.helpers import PASSWORD, become_owner, login_headers, register, run_sql


def test_register_returns_the_new_user(client):
    response = register(client, "new@example.com", first_name="  tejo ")

    assert response.status_code == 201
    user = response.json()
    assert user["email"] == "new@example.com"
    assert user["first_name"] == "Tejo"
    assert user["roles"] == ["customer"]
    assert isinstance(user["id"], str)
    assert "password_hash" not in user


@pytest.mark.parametrize(
    "password, message",
    [
        ("Ab1", "at least 8 characters"),
        ("password123", "uppercase letter"),
        ("PASSWORD123", "lowercase letter"),
        ("Password", "digit"),
    ],
)
def test_register_rejects_weak_passwords(client, password, message):
    response = register(client, "weak@example.com", password=password)

    assert response.status_code == 422
    assert message in response.json()["detail"][0]["msg"]


def test_register_rejects_duplicate_email(client):
    register(client, "dup@example.com")

    response = register(client, "dup@example.com")

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_register_as_owner_needs_a_phone(client):
    response = register(client, "owner@example.com", initial_role="car_owner")

    assert response.status_code == 400
    assert response.json()["detail"] == "Phone number is required for car owner accounts"


def test_register_as_owner_gets_both_roles(client):
    response = register(client, "owner@example.com", initial_role="car_owner", phone="9876543210")

    assert response.status_code == 201
    assert response.json()["roles"] == ["customer", "car_owner"]


@pytest.mark.parametrize("email, password", [
    ("user@example.com", "Wrong!123"),
    ("nobody@example.com", PASSWORD),
])
def test_bad_credentials_are_401_with_the_same_message(client, email, password):
    register(client, "user@example.com")

    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_requires_a_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials required"


@pytest.mark.parametrize("header", ["Bearer not-a-jwt", "Basic dXNlcjpwYXNz"])
def test_malformed_auth_headers_are_401(client, header):
    assert client.get("/auth/me", headers={"Authorization": header}).status_code == 401


def test_me_returns_the_logged_in_user(client):
    register(client, "me@example.com")
    headers = login_headers(client, "me@example.com")

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_login_cookie_alone_authenticates(client):
    register(client, "cookie@example.com")
    login = client.post("/auth/login", json={"email": "cookie@example.com", "password": PASSWORD})

    cookie = login.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert client.get("/auth/me").json()["email"] == "cookie@example.com"


def test_logout_clears_the_cookie_but_not_the_token(client):
    register(client, "out@example.com")
    login = client.post("/auth/login", json={"email": "out@example.com", "password": PASSWORD})
    token = login.json()["access_token"]

    client.post("/auth/logout")

    assert client.get("/auth/me").status_code == 401
    # JWTs are stateless: logout only removes the cookie, the token itself
    # stays valid until it expires.
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_verify_token(client, customer_headers):
    assert client.get("/auth/verify-token", headers=customer_headers).json()["valid"] is True
    assert client.get("/auth/verify-token", headers={"Authorization": "Bearer junk"}).json()["valid"] is False


def test_become_car_owner_requires_a_business_phone(client, customer_headers):
    response = client.post(
        "/auth/become-car-owner",
        json={"business_name": "Test Rentals"},
        headers=customer_headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "business_phone"]


def test_become_car_owner_twice_is_rejected(client, customer_headers):
    assert become_owner(client, customer_headers).status_code == 200

    response = become_owner(client, customer_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Already a car owner"
    assert client.get("/auth/me", headers=customer_headers).json()["roles"] == ["customer", "car_owner"]


# Roles and is_active are read from the database on every request, so these
# changes reach tokens that were issued before them.

def test_role_changes_apply_to_existing_tokens(client, customer_headers):
    assert client.get("/cars/mine", headers=customer_headers).status_code == 403

    assert become_owner(client, customer_headers).status_code == 200

    assert client.get("/cars/mine", headers=customer_headers).status_code == 200


def test_deactivated_user_is_locked_out(client, customer_headers):
    run_sql("UPDATE users SET is_active = false WHERE email = :email", email="customer@example.com")

    me = client.get("/auth/me", headers=customer_headers)
    login = client.post("/auth/login", json={"email": "customer@example.com", "password": PASSWORD})

    assert me.status_code == 403
    assert login.status_code == 400
    assert login.json()["detail"] == "Inactive user account"


def test_deleted_user_token_is_401(client, customer_headers):
    run_sql("DELETE FROM users WHERE email = :email", email="customer@example.com")

    response = client.get("/auth/me", headers=customer_headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "User not found or has been deleted"
