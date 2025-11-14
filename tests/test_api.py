"""
API endpoint'lerini test eder
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_chat_endpoint_success():
    """POST /api/chat başarılı yanıt"""
    response = client.post(
        "/api/chat",
        json={
            "message": "Merhaba",
            "session_id": "test_001"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["session_id"] == "test_001"
    assert len(data["response"]) > 0


def test_chat_endpoint_missing_fields():
    """POST /api/chat - eksik field"""
    response = client.post(
        "/api/chat",
        json={"message": "Test"}  # session_id eksik
    )
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_empty_message():
    """POST /api/chat - boş mesaj"""
    response = client.post(
        "/api/chat",
        json={"message": "", "session_id": "test_002"}
    )
    # Boş mesaj da kabul edilebilir, ama yanıt dönmeli
    assert response.status_code in [200, 422]


def test_websocket_connection():
    """WebSocket bağlantısı"""
    with client.websocket_connect("/ws?session_id=test_ws_1") as websocket:
        # Mesaj gönder
        websocket.send_text("Test mesajı")
        
        # Yanıt al
        data = websocket.receive_json()
        assert "response" in data or "type" in data


def test_home_page():
    """Ana sayfa erişimi"""
    response = client.get("/")
    # HTML döner veya 404 (eğer frontend yoksa)
    assert response.status_code in [200, 404]

