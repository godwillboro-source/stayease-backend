from .conftest import book, make_listing
from models import User


def test_admin_block_user_and_stats(client, admin_h, manager_h, customer_h):
    users = client.get("/api/admin/users?role=customer", headers=admin_h).get_json()["items"]
    customer_id = users[0]["id"]
    client.patch(f"/api/admin/users/{customer_id}", headers=admin_h, json={"is_active": False})
    assert client.get("/api/auth/me", headers=customer_h).status_code == 403
    assert client.post("/api/auth/login", json={"email": "carl@test.com", "password": "Password1!"}).status_code == 403

    stats = client.get("/api/admin/stats", headers=admin_h).get_json()
    assert stats["users"]["customers"] == 1 and stats["revenue"] == "0.00"


def test_admin_cannot_block_self(client, admin_h):
    me = client.get("/api/auth/me", headers=admin_h).get_json()
    assert client.patch(f"/api/admin/users/{me['id']}", headers=admin_h, json={"is_active": False}).status_code == 400


def test_non_admin_cannot_use_admin_routes(client, manager_h, customer_h):
    assert client.get("/api/admin/users", headers=manager_h).status_code == 403
    assert client.get("/api/admin/stats", headers=customer_h).status_code == 403


def test_admin_deletes_manager_and_related_property_data(client, admin_h, manager_h, customer_h):
    prop, unit = make_listing(client, manager_h, admin_h)
    booking = book(client, customer_h, unit["id"]).get_json()

    response = client.delete(f"/api/admin/users/{prop['manager_id']}", headers=admin_h)

    assert response.status_code == 204
    assert client.get(f"/api/properties/{prop['id']}", headers=admin_h).status_code == 404
    assert client.get(f"/api/units/{unit['id']}").status_code == 404
    assert client.get(f"/api/bookings/{booking['id']}", headers=admin_h).status_code == 404


def test_admin_deletes_customer_and_related_bookings(client, admin_h, manager_h, customer_h):
    _, unit = make_listing(client, manager_h, admin_h)
    booking = book(client, customer_h, unit["id"]).get_json()
    customer_id = client.get("/api/auth/me", headers=customer_h).get_json()["id"]

    response = client.delete(f"/api/admin/users/{customer_id}", headers=admin_h)

    assert response.status_code == 204
    assert client.get(f"/api/bookings/{booking['id']}", headers=admin_h).status_code == 404
    assert client.get(f"/api/units/{unit['id']}").status_code == 200


def test_admin_cannot_delete_admin_account(client, admin_h):
    admin_id = client.get("/api/auth/me", headers=admin_h).get_json()["id"]

    response = client.delete(f"/api/admin/users/{admin_id}", headers=admin_h)

    assert response.status_code == 400
    assert User.query.count() == 1


def test_non_admin_cannot_delete_user(client, manager_h, customer_h):
    customer_id = client.get("/api/auth/me", headers=customer_h).get_json()["id"]

    response = client.delete(f"/api/admin/users/{customer_id}", headers=manager_h)

    assert response.status_code == 403