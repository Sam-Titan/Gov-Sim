from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_listed_origin_only() -> None:
    ask = {"Access-Control-Request-Method": "GET"}
    ok = client.options("/api/health", headers={"Origin": "http://localhost:5173", **ask})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    other = client.options("/api/health", headers={"Origin": "https://evil.example", **ask})
    assert "access-control-allow-origin" not in other.headers
