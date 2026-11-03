import pytest

from tests.helpers import CAR, create_car

UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_malformed_car_id_is_422(client, owner_headers, method):
    kwargs = {"headers": owner_headers}
    if method == "patch":
        kwargs["json"] = {"daily_rate": "2000.00"}

    response = getattr(client, method)("/cars/abc", **kwargs)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "car_id"]


def test_unknown_car_is_404_with_its_message(client):
    response = client.get(f"/cars/{UNKNOWN_ID}")

    assert response.status_code == 404
    assert response.json()["message"] == "Car not found"


def test_customer_cannot_list_a_car(client, customer_headers):
    response = client.post("/cars", json=CAR, headers=customer_headers)

    assert response.status_code == 403


def test_owner_lists_a_car(client, owner_headers):
    response = client.post("/cars", json={**CAR, "make": "  Maruti "}, headers=owner_headers)

    assert response.status_code == 201
    car = response.json()
    assert car["make"] == "Maruti"
    assert car["daily_rate"] == "1800.00"
    assert car["is_active"] is True
    assert isinstance(car["owner_id"], str)


@pytest.mark.parametrize(
    "change, message",
    [
        ({"category": "spaceship"}, "Category must be one of"),
        ({"year": 1950}, "Year must be between"),
        ({"make": "   "}, "cannot be blank"),
        ({"daily_rate": "-5"}, "greater than 0"),
    ],
)
def test_create_rejects_invalid_cars(client, owner_headers, change, message):
    response = client.post("/cars", json={**CAR, **change}, headers=owner_headers)

    assert response.status_code == 422
    assert message in response.json()["detail"][0]["msg"]


def test_anyone_can_view_an_active_car(client, car):
    response = client.get(f"/cars/{car['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == car["id"]


def test_mine_lists_only_my_cars(client, car, owner_headers, other_owner_headers):
    other = create_car(client, other_owner_headers, model="Dzire")

    mine = client.get("/cars/mine", headers=owner_headers).json()
    theirs = client.get("/cars/mine", headers=other_owner_headers).json()

    assert [c["id"] for c in mine] == [car["id"]]
    assert [c["id"] for c in theirs] == [other["id"]]


def test_owner_updates_the_price(client, car, owner_headers):
    response = client.patch(f"/cars/{car['id']}", json={"daily_rate": "2000.00"}, headers=owner_headers)

    assert response.status_code == 200
    assert response.json()["daily_rate"] == "2000.00"


@pytest.mark.parametrize("field", ["make", "model", "year", "category", "city", "daily_rate", "is_active"])
def test_update_rejects_null_for_required_fields(client, car, owner_headers, field):
    response = client.patch(f"/cars/{car['id']}", json={field: None}, headers=owner_headers)

    assert response.status_code == 422
    assert "cannot be null" in response.json()["detail"][0]["msg"]


@pytest.mark.parametrize("field", ["make", "model", "city"])
def test_update_rejects_blank_text(client, car, owner_headers, field):
    response = client.patch(f"/cars/{car['id']}", json={field: "  "}, headers=owner_headers)

    assert response.status_code == 422
    assert "cannot be blank" in response.json()["detail"][0]["msg"]


def test_update_can_clear_the_description(client, car, owner_headers):
    client.patch(f"/cars/{car['id']}", json={"description": "Clean car"}, headers=owner_headers)

    response = client.patch(f"/cars/{car['id']}", json={"description": None}, headers=owner_headers)

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_update_needs_a_token(client, car):
    response = client.patch(f"/cars/{car['id']}", json={"daily_rate": "1.00"})

    assert response.status_code == 401


def test_another_owner_cannot_change_my_car(client, car, other_owner_headers):
    patched = client.patch(f"/cars/{car['id']}", json={"daily_rate": "1.00"}, headers=other_owner_headers)
    deleted = client.delete(f"/cars/{car['id']}", headers=other_owner_headers)

    assert patched.status_code == 403
    assert deleted.status_code == 403
    assert client.get(f"/cars/{car['id']}").json()["daily_rate"] == "1800.00"


def test_owner_deletes_their_car(client, car, owner_headers):
    response = client.delete(f"/cars/{car['id']}", headers=owner_headers)

    assert response.status_code == 204
    assert client.get(f"/cars/{car['id']}").status_code == 404
    assert client.get("/cars/mine", headers=owner_headers).json() == []


def test_inactive_cars_are_hidden_until_reactivated(client, car, owner_headers):
    client.patch(f"/cars/{car['id']}", json={"is_active": False}, headers=owner_headers)

    assert client.get("/cars").json() == []
    assert client.get(f"/cars/{car['id']}").status_code == 404
    assert len(client.get("/cars/mine", headers=owner_headers).json()) == 1

    response = client.patch(f"/cars/{car['id']}", json={"is_active": True}, headers=owner_headers)

    assert response.status_code == 200
    assert [c["id"] for c in client.get("/cars").json()] == [car["id"]]


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"city": "hyder"}, {"Swift", "Creta"}),
        ({"category": "suv"}, {"Creta"}),
        ({"min_price": "2000"}, {"Creta"}),
        ({"max_price": "2000"}, {"Swift", "Nexon"}),
        ({"city": "pune", "category": "hatchback"}, {"Nexon"}),
    ],
)
def test_browse_filters(client, owner_headers, params, expected):
    create_car(client, owner_headers)
    create_car(client, owner_headers, model="Creta", category="suv", daily_rate="3500.00")
    create_car(client, owner_headers, model="Nexon", city="Pune")

    response = client.get("/cars", params=params)

    assert {c["model"] for c in response.json()} == expected


def test_browse_pages_are_newest_first_and_never_overlap(client, owner_headers):
    for model in ["Swift", "Dzire", "Baleno"]:
        create_car(client, owner_headers, model=model)

    pages = [client.get("/cars", params={"skip": skip, "limit": 1}).json() for skip in range(3)]

    assert [page[0]["model"] for page in pages] == ["Baleno", "Dzire", "Swift"]


@pytest.mark.parametrize("params", [{"limit": 101}, {"limit": 0}, {"skip": -1}, {"min_price": "-1"}])
def test_browse_rejects_out_of_range_params(client, params):
    assert client.get("/cars", params=params).status_code == 422
