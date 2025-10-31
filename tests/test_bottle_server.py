"""
Tests for the Bottle-based server.
These tests verify that the server launches correctly and handles routes.
"""
import pytest
from drafter import Server, route, Page


class TestBottleServer:
    """Test suite for the Bottle server."""

    def test_server_initialization(self):
        """Test that a Server can be initialized."""
        server = Server(_custom_name="TEST_SERVER")
        assert server is not None
        assert server._custom_name == "TEST_SERVER"

    def test_server_has_routes_dict(self):
        """Test that a Server has a routes dictionary."""
        server = Server(_custom_name="TEST_SERVER")
        assert hasattr(server, "routes")
        assert isinstance(server.routes, dict)

    def test_server_add_route(self):
        """Test adding a route to the server."""
        server = Server(_custom_name="TEST_SERVER")
        
        def test_route(state):
            return Page(state, ["Test page"])
        
        server.add_route("test", test_route)
        assert "test" in server.routes
        assert server.routes["test"] == test_route

    def test_server_setup(self):
        """Test server setup with initial state."""
        server = Server(_custom_name="TEST_SERVER")
        initial_state = {"count": 0}
        server.setup(initial_state)
        # After setup, the server should have the initial state
        assert server._state is not None

    def test_route_decorator_basic(self):
        """Test basic route decorator usage."""
        server = Server(_custom_name="TEST_SERVER")
        
        @route("index", server=server)
        def index(state):
            return Page(state, ["Index page"])
        
        assert "index" in server.routes
        assert server.routes["index"] == index

    def test_route_decorator_function_name(self):
        """Test route decorator using function name as URL."""
        server = Server(_custom_name="TEST_SERVER")
        
        @route(server=server)
        def my_page(state):
            return Page(state, ["My page"])
        
        assert "my_page" in server.routes

    def test_server_configuration(self):
        """Test that server has configuration."""
        server = Server(_custom_name="TEST_SERVER")
        assert hasattr(server, "configuration")

    def test_server_state_management(self):
        """Test basic state management."""
        server = Server(_custom_name="TEST_SERVER")
        test_state = {"value": 42}
        server.setup(test_state)
        # State should be set after setup
        assert server._state is not None

    def test_multiple_routes(self):
        """Test adding multiple routes to the same server."""
        server = Server(_custom_name="TEST_SERVER")
        
        @route("page1", server=server)
        def page1(state):
            return Page(state, ["Page 1"])
        
        @route("page2", server=server)
        def page2(state):
            return Page(state, ["Page 2"])
        
        assert len(server.routes) == 2
        assert "page1" in server.routes
        assert "page2" in server.routes

    def test_server_has_app(self):
        """Test that server can have a Bottle app after setup."""
        server = Server(_custom_name="TEST_SERVER")
        server.setup()
        # After setup, the server may have an app
        assert hasattr(server, "app")
