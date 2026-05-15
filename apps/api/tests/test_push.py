"""Push token register/list/delete + ownership boundary."""
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def _fake_token() -> str:
    return f"ExponentPushToken[test-{uuid4().hex[:12]}]"


def test_register_returns_persisted_token(client: TestClient) -> None:
    _, token = register_user(client)
    expo = _fake_token()

    response = client.post(
        "/api/v1/push/register",
        headers=auth_headers(token),
        json={"expo_token": expo, "device_label": "pytest"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["expo_token"] == expo
    assert body["device_label"] == "pytest"
    assert body["last_seen"] is not None


def test_register_upsert_rebinds_to_caller(client: TestClient) -> None:
    expo = _fake_token()
    _, first = register_user(client)
    _, second = register_user(client)

    client.post(
        "/api/v1/push/register",
        headers=auth_headers(first),
        json={"expo_token": expo, "device_label": "first"},
    )
    response = client.post(
        "/api/v1/push/register",
        headers=auth_headers(second),
        json={"expo_token": expo, "device_label": "second"},
    )
    assert response.status_code == 201

    # First user should no longer see this token in their listing.
    listing_first = client.get("/api/v1/push/me", headers=auth_headers(first))
    assert listing_first.status_code == 200
    assert all(t["expo_token"] != expo for t in listing_first.json())

    # Second user should.
    listing_second = client.get("/api/v1/push/me", headers=auth_headers(second))
    tokens = [t["expo_token"] for t in listing_second.json()]
    assert expo in tokens


def test_user_cannot_delete_other_users_token(client: TestClient) -> None:
    expo = _fake_token()
    _, owner = register_user(client)
    _, attacker = register_user(client)

    client.post(
        "/api/v1/push/register",
        headers=auth_headers(owner),
        json={"expo_token": expo},
    )

    response = client.delete(
        f"/api/v1/push/{expo}", headers=auth_headers(attacker)
    )
    assert response.status_code == 404  # hides existence


def test_owner_can_delete_own_token(client: TestClient) -> None:
    expo = _fake_token()
    _, owner = register_user(client)
    client.post(
        "/api/v1/push/register",
        headers=auth_headers(owner),
        json={"expo_token": expo},
    )
    response = client.delete(
        f"/api/v1/push/{expo}", headers=auth_headers(owner)
    )
    assert response.status_code == 204
