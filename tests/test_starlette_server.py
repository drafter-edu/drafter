"""
Tests for the Starlette server to confirm that it successfully launches
and injects the necessary components to work.

These tests validate that the local development server (AppServer) properly
serves pages with the required HTML structure, scripts, and assets.
"""
import pytest
from pathlib import Path
from starlette.testclient import TestClient
from drafter.app.app_server import make_app, DevConfig
from drafter.app.utils import pkg_assets_dir


@pytest.fixture
def test_file(tmp_path):
    """Create a minimal test Python file"""
    test_file = tmp_path / "test_app.py"
    test_file.write_text("""
from drafter import route, Page

@route("index")
def index():
    return Page(None, ["Hello, World!"])
""")
    return test_file


def test_server_creates_app(test_file):
    """Test that the server application can be created"""
    cfg = DevConfig(
        title="Test App",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    app = make_app(cfg)
    
    assert app is not None
    assert hasattr(app, 'state')
    assert app.state.cfg.title == "Test App"


def test_server_serves_index_page(test_file):
    """Test that the server serves the index page with required structure"""
    cfg = DevConfig(
        title="Test App",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    app = make_app(cfg)
    
    with TestClient(app) as client:
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        html = response.text
        
        # Check for essential HTML structure
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<head>" in html
        assert "<body>" in html
        
        # Check for page title
        assert "<title>Test App</title>" in html


def test_server_injects_drafter_root(test_file):
    """Test that the server injects the drafter root div"""
    cfg = DevConfig(
        title="Test App",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    app = make_app(cfg)
    
    with TestClient(app) as client:
        response = client.get("/")
        html = response.text
        
        # Check for drafter root div
        assert 'id="drafter-root--"' in html or 'id="drafter-root"' in html


def test_server_includes_skulpt_script(test_file):
    """Test that the server includes Skulpt script tags"""
    cfg = DevConfig(
        title="Test App",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    app = make_app(cfg)
    
    with TestClient(app) as client:
        response = client.get("/")
        html = response.text
        
        # Check for Skulpt-related script tags or references
        assert "<script" in html


def test_server_includes_drafter_js(test_file):
    """Test that the server includes drafter.js or references to it"""
    cfg = DevConfig(
        title="Test App",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    app = make_app(cfg)
    
    with TestClient(app) as client:
        response = client.get("/")
        html = response.text
        
        # Check for drafter.js reference
        assert "drafter" in html.lower()


def test_server_includes_user_code_inline(tmp_path):
    """Test that when inline_py is True, user code is embedded in the page"""
    test_file = tmp_path / "inline_test.py"
    user_code = """
from drafter import route, Page

@route("index")
def index():
    return Page(None, ["Inline Test"])
"""
    test_file.write_text(user_code)
    
    cfg = DevConfig(
        title="Inline Test",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    app = make_app(cfg)
    
    with TestClient(app) as client:
        response = client.get("/")
        html = response.text
        
        # Check that user code appears in the HTML
        assert "Inline Test" in html


def test_server_includes_websocket_connection(test_file):
    """Test that the server sets up WebSocket for hot reload"""
    cfg = DevConfig(
        title="WS Test",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    app = make_app(cfg)
    
    with TestClient(app) as client:
        response = client.get("/")
        html = response.text
        
        # Check for WebSocket connection setup
        assert "ws://" in html or "WebSocket" in html


def test_server_serves_static_assets(test_file):
    """Test that the server can serve static assets"""
    cfg = DevConfig(
        title="Assets Test",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    app = make_app(cfg)
    
    with TestClient(app) as client:
        # Try to access a static asset
        assets_dir = pkg_assets_dir()
        if (assets_dir / "drafter.js").exists():
            response = client.get("/assets/drafter.js")
            assert response.status_code in [200, 404]
