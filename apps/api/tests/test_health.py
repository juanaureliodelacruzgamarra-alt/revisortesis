from fastapi.testclient import TestClient

from kimy.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Aurelio API"
    assert "version" in body


def test_root_returns_service_metadata():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "Aurelio API"
    assert body["docs"] == "/docs"
