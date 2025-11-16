"""Integration tests covering the FastAPI surface area."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"


def test_metrics_endpoint_structure(client: TestClient) -> None:
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert {"uptime_seconds", "total_messages", "sessions"}.issubset(data)


def test_chat_endpoint_success(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={"message": "Merhaba", "session_id": "integration-1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "integration-1"
    assert payload["response"]


def test_chat_endpoint_validation_error(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": "Eksik"})
    assert response.status_code == 422


def test_websocket_roundtrip(client: TestClient) -> None:
    with client.websocket_connect("/ws?session_id=ws-case") as websocket:
        websocket.send_text("İade politikası nedir?")
        message = websocket.receive_json()
        assert message["type"] == "response"
        assert "response" in message
        assert message["session_id"] == "ws-case"


def test_home_page_served_or_missing(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code in {200, 404}
