from sqlalchemy import text

from app.database import engine

PASSWORD = "Passw0rd!23"

CAR = {
    "make": "Maruti",
    "model": "Swift",
    "year": 2022,
    "category": "hatchback",
    "city": "Hyderabad",
    "daily_rate": "1800.00",
}


def register(client, email, **overrides):
    body = {"email": email, "password": PASSWORD, "first_name": "Test", "last_name": "User"}
    body.update(overrides)
    return client.post("/auth/register", json=body)


def login_headers(client, email, password=PASSWORD):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    # Login also sets the auth cookie on the client; drop it so every test
    # authenticates only through the headers it passes explicitly.
    client.cookies.clear()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def become_owner(client, headers):
    return client.post(
        "/auth/become-car-owner",
        json={"business_name": "Test Rentals", "business_phone": "9876543210"},
        headers=headers,
    )


def make_owner(client, email):
    register(client, email)
    headers = login_headers(client, email)
    response = become_owner(client, headers)
    assert response.status_code == 200, response.text
    return headers


def create_car(client, headers, **changes):
    response = client.post("/cars", json={**CAR, **changes}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def run_sql(sql, **params):
    with engine.begin() as conn:
        conn.execute(text(sql), params)
