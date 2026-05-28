from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data

def test_api_metrics():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data
    assert "completed_calls" in data
    assert "average_score" in data

def test_api_calls_empty():
    response = client.get("/api/v1/calls")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
