from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_contract():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_invalid_filters_are_rejected():
    assert client.get("/api/overview?platform=NotAPlatform").status_code == 422
    assert client.get("/api/overview?start_date=2025-02-01&end_date=2025-01-01").status_code == 422
