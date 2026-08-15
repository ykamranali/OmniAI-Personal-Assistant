import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket_unrecognized():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("hello")
        data = websocket.receive_json()
        assert data["type"] == "stream_start"
