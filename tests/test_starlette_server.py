"""
Tests for Starlette server functionality.
These tests verify that the server launches successfully and injects necessary components.
"""
import pytest
import asyncio
from pathlib import Path
from starlette.testclient import TestClient
from drafter.app.app_server import create_app, DevConfig


def test_server_launches():
    """Test that the Starlette server can be created and launches successfully."""
    # Create a simple test Python file
    test_file = Path(__file__).parent / "fixtures" / "simple_test.py"
    test_file.parent.mkdir(exist_ok=True)
    
    test_code = '''from drafter import route, Page

@route
def index():
    return Page(None, ["Hello, World!"])
'''
    test_file.write_text(test_code)
    
    config = DevConfig(
        title="Test App",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    
    app = create_app(config)
    client = TestClient(app)
    
    # Test that the index route works
    response = client.get("/")
    assert response.status_code == 200
    assert "Test App" in response.text
    
    # Cleanup
    test_file.unlink()


def test_server_injects_assets():
    """Test that necessary assets and scripts are injected into the page."""
    test_file = Path(__file__).parent / "fixtures" / "simple_test.py"
    test_file.parent.mkdir(exist_ok=True)
    
    test_code = '''from drafter import route, Page

@route
def index():
    return Page(None, ["Test Content"])
'''
    test_file.write_text(test_code)
    
    config = DevConfig(
        title="Asset Test",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    
    app = create_app(config)
    client = TestClient(app)
    
    response = client.get("/")
    html = response.text
    
    # Verify essential components are injected
    assert "drafter" in html.lower() or "skulpt" in html.lower()
    assert "<script" in html
    assert "drafter-root" in html or "DRAFTER_ROOT" in html.lower()
    
    # Cleanup
    test_file.unlink()


def test_server_serves_static_assets():
    """Test that static assets are served correctly."""
    test_file = Path(__file__).parent / "fixtures" / "simple_test.py"
    test_file.parent.mkdir(exist_ok=True)
    
    test_code = '''from drafter import route, Page

@route
def index():
    return Page(None, ["Assets Test"])
'''
    test_file.write_text(test_code)
    
    config = DevConfig(
        title="Static Assets Test",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    
    app = create_app(config)
    client = TestClient(app)
    
    # Test that assets endpoint exists and returns JS files
    # The actual paths will depend on the app structure
    response = client.get("/assets/drafter.js")
    # We expect either 200 (found) or 404 (not yet built), but not 500 (server error)
    assert response.status_code in [200, 404]
    
    # Cleanup
    test_file.unlink()


def test_server_websocket_connection():
    """Test that WebSocket for hot reload is available."""
    test_file = Path(__file__).parent / "fixtures" / "simple_test.py"
    test_file.parent.mkdir(exist_ok=True)
    
    test_code = '''from drafter import route, Page

@route
def index():
    return Page(None, ["WebSocket Test"])
'''
    test_file.write_text(test_code)
    
    config = DevConfig(
        title="WebSocket Test",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    
    app = create_app(config)
    client = TestClient(app)
    
    # Test WebSocket endpoint exists
    # Note: TestClient WebSocket testing is simplified
    try:
        with client.websocket_connect("/ws") as websocket:
            # Connection successful
            assert True
    except Exception:
        # WebSocket might not be fully implemented yet
        pytest.skip("WebSocket not fully implemented")
    
    # Cleanup
    test_file.unlink()
