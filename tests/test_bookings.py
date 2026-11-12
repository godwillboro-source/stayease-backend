from .conftest import book, login, make_listing, register

def test_booking_flow_and_availability(client, manager_h, admin_h, customer_h):
    _, unit = make_listing(client, manager_h, admin_h, price="20000.00")
    res = book(client, customer_h, unit["id"])
    assert res.status_code == 201
    booking = res.get_json()
    assert booking["status"] == "pending"
    assert booking["total_price"] == "60000.00"
    
    assert client.get("/api/bookings", headers=manager_h).get_json()["total"] == 1
    res = client.patch(f"/api/bookings/{booking['id']}/status", headers=manager_h, json={"status": "confirmed"})
    assert res.status_code == 200
    assert client.get(f"/api/units/{unit['id']}").get_json()["available_units"] == 1

    res = client.patch(f"/api/bookings/{booking['id']}/status", headers=customer_h, json={"status": "cancelled"})
    assert res.status_code == 200
    assert client.get(f"/api/units/{unit['id']}").get_json()["available_units"] == 2

    res = client.patch(f"/api/bookings/{booking['id']}/status", headers=manager_h, json={"status": "confirmed"})
    assert res.status_code == 409