import pytest
import sys
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Mock pyautogui to prevent GUI display/import errors during tests
mock_pyautogui = MagicMock()
sys.modules["pyautogui"] = mock_pyautogui

from fastapi.testclient import TestClient
from app.main import app
from app.agents.base import agent_manager
from app.plugins.manager import plugin_manager

# Ensure plugins are loaded
plugin_manager.load_plugins()

@pytest.fixture
def ws_client():
    return TestClient(app)

def test_websocket_routing_unrecognized(ws_client):
    with ws_client.websocket_connect("/ws") as websocket:
        websocket.send_text("unknown command 12345")
        data = websocket.receive_json()
        assert data["type"] == "stream_start"

@patch("app.agents.browser_agent.async_playwright")
def test_websocket_routing_browser(mock_async_playwright, ws_client):
    # Setup mocks for Playwright browser and page
    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    
    mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_page.title = AsyncMock(return_value="Google")
    
    with ws_client.websocket_connect("/ws") as websocket:
        # Send request matching BrowserAgent
        websocket.send_text(json.dumps({"request": "go to www.google.com"}))
        data = websocket.receive_json()
        
        assert data["status"] == "success"
        assert "Navigated to https://www.google.com" in data["message"]
        assert data["data"]["title"] == "Google"
        assert data["data"]["url"] == "https://www.google.com"
        
        mock_page.goto.assert_called_with("https://www.google.com")

@patch("app.agents.os_agent.llm_service")
def test_websocket_routing_os_screenshot(mock_llm, ws_client):
    mock_pyautogui.screenshot = MagicMock()
    # Mock LLM to return a 'done' command to exit the loop
    mock_llm.generate_chat_response = AsyncMock(return_value='{"action": "done", "message": "Screenshot saved to Downloads."}')
    
    with ws_client.websocket_connect("/ws") as websocket:
        websocket.send_text(json.dumps({"type": "config", "os_control_allowed": True}))
        websocket.send_text("take screenshot")
        data = websocket.receive_json()
        
        assert data["status"] == "success"
        assert "Screenshot saved" in data["message"]
        mock_pyautogui.screenshot.assert_called_once()
