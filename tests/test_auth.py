from unittest.mock import patch

from .conftest import login, register


def test_register_login_me(client):
    res = register(client, "Carl", "carl@test.com", "customer")
    assert res.status_code == 201
    assert "password" not in res.get_json()["user"]
    assert register(client, "Carl", "carl@test.com", "customer").status_code == 409
    h = login(client, "carl@test.com")
    user = client.get("/api/auth/me", headers=h).get_json()
    assert set(user) == {"id", "name", "role"}
    assert user["name"] == "Carl"
    assert user["role"] == "customer"


def test_register_sends_welcome_email(client):
    with patch("routes.auth.send_welcome_email") as send_welcome:
        response = register(client, "Carl", "carl@test.com", "customer")

    assert response.status_code == 201
    assert response.get_json()["email_sent"] is True
    send_welcome.assert_called_once_with("carl@test.com", "Carl")


def test_login_sends_sign_in_notification(client):
    register(client, "Carl", "carl@test.com", "customer")
    with patch("routes.auth.send_sign_in_notification") as send_notification:
        response = client.post(
            "/api/auth/login",
            json={"email": "carl@test.com", "password": "Password1!"},
        )

    assert response.status_code == 200
    assert response.get_json()["email_notification_sent"] is True
    send_notification.assert_called_once_with("carl@test.com", "Carl")


def test_email_delivery_failure_is_reported_without_blocking_auth(client):
    from email_service import EmailDeliveryError

    with patch("routes.auth.send_welcome_email", side_effect=EmailDeliveryError("Resend is not configured")):
        registration = register(client, "Carl", "carl@test.com", "customer")

    assert registration.status_code == 201
    assert registration.get_json()["email_sent"] is False

    with patch("routes.auth.send_sign_in_notification", side_effect=EmailDeliveryError("Resend is not configured")):
        response = client.post(
            "/api/auth/login",
            json={"email": "carl@test.com", "password": "Password1!"},
        )

    assert response.status_code == 200
    assert response.get_json()["email_notification_sent"] is False


def test_cannot_register_as_admin(client):
    assert register(client, "Evil", "evil@test.com", "admin").status_code == 400


def test_bad_login(client):
    assert client.post("/api/auth/login", json={"email": "x@test.com", "password": "nope12345"}).status_code == 401


def test_login_returns_minimal_user(client):
    register(client, "Carl", "carl@test.com", "customer")
    response = client.post(
        "/api/auth/login",
        json={"email": "carl@test.com", "password": "Password1!"},
    )

    assert response.status_code == 200
    user = response.get_json()["user"]
    assert set(user) == {"id", "name", "role"}
    assert user["id"] > 0
    assert user["name"] == "Carl"
    assert user["role"] == "customer"


def test_protected_route_needs_session(client):
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_session(client):
    register(client, "Carl", "carl@test.com", "customer")
    response = client.post(
        "/api/auth/login",
        json={"email": "carl@test.com", "password": "Password1!"},
    )

    assert response.status_code == 200
    assert "access_token" not in response.get_json()
    cookie = response.headers["Set-Cookie"].split(";", 1)[0]
    assert client.get("/api/auth/me", headers={"Cookie": cookie}).status_code == 200

    response = client.post("/api/auth/logout", headers={"Cookie": cookie})

    assert response.status_code == 200
    assert response.headers["Set-Cookie"].startswith("session=;")
    assert client.get("/api/auth/me").status_code == 401