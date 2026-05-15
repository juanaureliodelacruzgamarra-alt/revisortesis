"""Submissions: list scoping, create, role boundaries."""
from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def _ensure_program(client: TestClient, admin_token: str) -> str:
    """Return an existing program id, or create one. Idempotent."""
    list_response = client.get(
        "/api/v1/programs", headers=auth_headers(admin_token)
    )
    assert list_response.status_code == 200
    programs = list_response.json()
    if programs:
        return programs[0]["id"]
    create_response = client.post(
        "/api/v1/programs",
        headers=auth_headers(admin_token),
        json={
            "name": "Maestria de prueba",
            "code": f"TEST{len(programs)}",
            "level": "masters",
        },
    )
    assert create_response.status_code == 201, create_response.text
    return create_response.json()["id"]


def test_student_creates_submission_and_lists_own(client: TestClient) -> None:
    _, admin_token = register_user(client, role="admin")
    program_id = _ensure_program(client, admin_token)
    _, student_token = register_user(client, role="student")

    create = client.post(
        "/api/v1/submissions",
        headers=auth_headers(student_token),
        json={
            "program_id": program_id,
            "title": "Avance test e2e",
            "chapter": "Capitulo 1",
        },
    )
    assert create.status_code == 201, create.text
    submission_id = create.json()["id"]
    assert create.json()["status"] == "draft"
    assert create.json()["versions"] == []

    listing = client.get(
        "/api/v1/submissions", headers=auth_headers(student_token)
    )
    assert listing.status_code == 200
    ids = [s["id"] for s in listing.json()]
    assert submission_id in ids


def test_advisor_cannot_create_submission(client: TestClient) -> None:
    _, admin_token = register_user(client, role="admin")
    program_id = _ensure_program(client, admin_token)
    _, advisor_token = register_user(client, role="advisor")

    response = client.post(
        "/api/v1/submissions",
        headers=auth_headers(advisor_token),
        json={
            "program_id": program_id,
            "title": "Should fail",
        },
    )
    assert response.status_code == 403


def test_student_cannot_see_others_submission(client: TestClient) -> None:
    _, admin_token = register_user(client, role="admin")
    program_id = _ensure_program(client, admin_token)
    _, student_a = register_user(client, role="student")
    _, student_b = register_user(client, role="student")

    create = client.post(
        "/api/v1/submissions",
        headers=auth_headers(student_a),
        json={"program_id": program_id, "title": "Private to A"},
    )
    submission_id = create.json()["id"]

    # B should get 403 (or 404 — both are acceptable hide-the-existence
    # responses; we accept either).
    response = client.get(
        f"/api/v1/submissions/{submission_id}",
        headers=auth_headers(student_b),
    )
    assert response.status_code in (403, 404)


def test_admin_lists_eligible_advisors(client: TestClient) -> None:
    _, admin_token = register_user(client, role="admin")
    # Make sure at least one advisor exists.
    register_user(client, role="advisor")

    response = client.get(
        "/api/v1/submissions/advisors", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        sample = data[0]
        assert "id" in sample
        assert "full_name" in sample
        assert "orcid_linked" in sample
