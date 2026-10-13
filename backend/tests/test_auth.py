from pathlib import Path

import pytest

from tests.conftest import USER_EMAIL, USER_PASSWORD


def test_register_and_login_with_form(client, registered_user):
    assert registered_user["email"] == USER_EMAIL

    response = client.post(
        "/api/auth/login",
        data={"username": USER_EMAIL, "password": USER_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_login_json(client, registered_user):
    response = client.post(
        "/api/auth/login-json",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client, registered_user):
    response = client.post(
        "/api/auth/login",
        data={"username": USER_EMAIL, "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_token_grants_access_to_me(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == USER_EMAIL


@pytest.mark.parametrize(
    "path, payload",
    [
        ("/api/auth/forgot-password", {"email": USER_EMAIL}),
        (
            "/api/auth/forgot-password/verify",
            {"email": USER_EMAIL, "otp": "123456", "new_password": "attacker-password"},
        ),
    ],
)
def test_password_reset_endpoints_are_disabled(client, registered_user, path, payload):
    response = client.post(path, json=payload)

    assert response.status_code == 501


def test_old_hardcoded_otp_cannot_take_over_account(client, registered_user):
    client.post("/api/auth/forgot-password", json={"email": USER_EMAIL})
    client.post(
        "/api/auth/forgot-password/verify",
        json={"email": USER_EMAIL, "otp": "123456", "new_password": "attacker-password"},
    )

    attacker = client.post(
        "/api/auth/login",
        data={"username": USER_EMAIL, "password": "attacker-password"},
    )
    owner = client.post(
        "/api/auth/login",
        data={"username": USER_EMAIL, "password": USER_PASSWORD},
    )

    assert attacker.status_code == 401
    assert owner.status_code == 200


def test_no_hardcoded_reset_code_in_auth_routes():
    source = (Path(__file__).parents[1] / "app" / "api" / "routes" / "auth.py").read_text()

    assert "123456" not in source
    assert "_otp_store" not in source

 
def test_user_can_save_and_clear_telegram_chat_id(client, auth_headers):
    saved = client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"telegram_chat_id": "123456789"},
    )
    assert saved.status_code == 200
    assert saved.json()["telegram_chat_id"] == "123456789"

    cleared = client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"telegram_chat_id": ""},
    )
    assert cleared.status_code == 200
    assert cleared.json()["telegram_chat_id"] is None
