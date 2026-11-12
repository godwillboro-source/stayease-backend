from .conftest import book, login, make_listing, register

def test_booking_flow_and_availability(client, manager_h, admin_h, customer_h):
    _, unit = make_listing(client, manager_h, admin_h, price="20000.00")
    res = book(client, customer_h, unit["id"])
    assert res.status_code == 201
    booking = res.get_json()
    assert booking["status"] == "pending"
    assert booking["total_price"] == "60000.00"