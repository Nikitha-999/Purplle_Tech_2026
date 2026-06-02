# PROMPT: Generate pytest tests for GET /health on a FastAPI Store Intelligence API
# using SQLite in a temp file, expecting status ok, database up, and ST1008 store seeded.
# CHANGES MADE: Database reset and store seeding moved to tests/conftest.py for isolation.

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["database"] == "up"
        assert body["status"] in ("ok", "degraded")
        assert body["version"] == "0.1.0"


def test_health_lists_seeded_store():
    with TestClient(app) as client:
        response = client.get("/health")
        stores = {item["store_id"] for item in response.json()["stores"]}
        assert "ST1008" in stores


def test_root_endpoint():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["health"] == "/health"
