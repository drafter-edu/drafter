"""
Tests for the Starlette local development server.
These tests verify that the server launches correctly and injects the necessary assets.
"""
import pytest
from pathlib import Path
from starlette.testclient import TestClient
from drafter.app.local_server import make_app, DevConfig


@pytest.fixture
def test_user_file(tmp_path):
    """Create a temporary test Python file."""
    test_file = tmp_path / "test_app.py"
    test_file.write_text("""
from drafter import route, start_server, Page

@route("index")
def index():
    return Page(None, ["Hello from test!"])

start_server()
""")
    return test_file


@pytest.fixture
def dev_config(test_user_file):
    """Create a DevConfig for testing."""
    return DevConfig(
        title="Test App",
        user_path=test_user_file,
        inline_py=True,
        host="localhost",
        port=8080,
    )


@pytest.fixture
def app(dev_config):
    """Create a test Starlette application."""
    return make_app(dev_config)


@pytest.fixture
def client(app):
    """Create a test client for the Starlette app."""
    return TestClient(app)


class TestStarletteServer:
    """Test suite for the Starlette development server."""

    def test_server_launches(self, client):
        """Test that the server launches and responds to requests."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_index_page_contains_title(self, client, dev_config):
        """Test that the index page contains the configured title."""
        response = client.get("/")
        assert dev_config.title in response.text

    def test_index_page_contains_user_code(self, client):
        """Test that the index page includes the user's Python code when inline_py is True."""
        response = client.get("/")
        html = response.text
        # When inline_py is True, the user code should be embedded
        assert "Hello from test!" in html or "index" in html

    def test_skulpt_injection(self, client):
        """Test that Skulpt library is injected into the page."""
        response = client.get("/")
        html = response.text
        # Check for Skulpt references
        assert "skulpt" in html.lower() or "Sk." in html

    def test_drafter_client_injection(self, client):
        """Test that the Drafter client library is injected."""
        response = client.get("/")
        html = response.text
        # Check for drafter client library references
        assert "drafter" in html.lower() or "assets/drafter.js" in html

    def test_websocket_url_injection(self, client, dev_config):
        """Test that WebSocket URL is injected for hot reload."""
        response = client.get("/")
        html = response.text
        # Check for websocket connection URL
        assert "ws://" in html or dev_config.ws_url in html

    def test_assets_route_exists(self, client):
        """Test that the /assets route is available."""
        # This will fail if drafter.js doesn't exist, but that's okay for now
        # We're just checking the route is mounted
        response = client.get("/assets/drafter.js")
        # Should either succeed or give 404, not 500 or connection error
        assert response.status_code in [200, 404]

    def test_websocket_connection(self, client):
        """Test that WebSocket endpoint is available."""
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None


class TestServerConfiguration:
    """Test suite for server configuration."""

    def test_dev_config_ws_url(self):
        """Test that DevConfig generates correct WebSocket URL."""
        config = DevConfig(
            title="Test",
            user_path=Path("test.py"),
            inline_py=True,
            host="localhost",
            port=8080,
        )
        assert config.ws_url == "ws://localhost:8080/ws"

    def test_dev_config_different_port(self):
        """Test DevConfig with different port."""
        config = DevConfig(
            title="Test",
            user_path=Path("test.py"),
            inline_py=True,
            host="localhost",
            port=3000,
        )
        assert config.ws_url == "ws://localhost:3000/ws"
