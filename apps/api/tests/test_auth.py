"""Auth flow: register, duplicate detection, login, /me, refresh, role gates."""
from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user, unique_email


def test_register_returns_token_pair(client: TestClient) -> None:
    email = unique_email()
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "GoodPass123",
            "full_name": "Test User",
            "role": "student",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] == 900  # 15 min


def test_duplicate_email_returns_409(client: TestClient) -> None:
    email, _ = register_user(client)
    second = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "GoodPass123",
            "full_name": "Another",
            "role": "student",
        },
    )
    assert second.status_code == 409
    assert "already" in second.json()["detail"].lower()


def test_short_password_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email(),
            "password": "short",
            "full_name": "Test",
            "role": "student",
        },
    )
    assert response.status_code == 422


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    email, _ = register_user(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongPassword999"},
    )
    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient) -> None:
    email, token = register_user(client, role="advisor")
    response = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == email
    assert body["role"] == "advisor"
    assert body["is_active"] is True


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_returns_new_access_token(client: TestClient) -> None:
    email = unique_email()
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "GoodPass123",
            "full_name": "Refresher",
            "role": "student",
        },
    )
    refresh = register_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["expires_in"] == 900


def test_refresh_with_access_token_rejected(client: TestClient) -> None:
    _, access = register_user(client)
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access}
    )
    # The access token has type=access, refresh endpoint expects type=refresh.
    assert response.status_code == 401


def test_student_cannot_access_admin_endpoint(client: TestClient) -> None:
    _, student_token = register_user(client, role="student")
    response = client.get(
        "/api/v1/admin/fine-tuning/stats", headers=auth_headers(student_token)
    )
    assert response.status_code == 403


def test_coordinator_cannot_access_admin_only(client: TestClient) -> None:
    _, coord_token = register_user(client, role="coordinator")
    # The fine-tuning router is admin-only.
    response = client.get(
        "/api/v1/admin/fine-tuning/stats", headers=auth_headers(coord_token)
    )
    assert response.status_code == 403


def test_admin_can_access_admin_endpoint(client: TestClient) -> None:
    _, admin_token = register_user(client, role="admin")
    response = client.get(
        "/api/v1/admin/fine-tuning/stats", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert "total_eligible" in body
    assert "min_examples_threshold" in body
