"""Test fixtures.

The KIMY test suite is intentionally *black-box*: it hits the FastAPI app
through ``TestClient`` against the same Postgres+pgvector instance the dev
stack uses. We don't try to isolate via SQLite (pgvector and JSONB are
required) — instead each test creates uniquely-named users via ``unique_email``
so runs don't collide, and we never assert against pre-existing data.

CI spins up its own Postgres service, so the same fixtures work end-to-end.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from uuid import uuid4

# Disable rate limiting before the app module is imported — otherwise we'd hit
# the 5/min register cap inside the suite.
os.environ.setdefault("RATE_LIMIT_DISABLED", "1")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from kimy.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Reusable TestClient — the FastAPI app handles its own DB lifecycle."""
    with TestClient(app) as c:
        yield c


def unique_email(role: str = "student") -> str:
    return f"test-{role}-{uuid4().hex[:10]}@test.kimy"


def register_user(
    client: TestClient,
    *,
    role: str = "student",
    password: str = "TestPass1234",
) -> tuple[str, str]:
    """Create a fresh user and return (email, access_token)."""
    email = unique_email(role)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"Test {role.title()} {email}",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return email, token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
