"""
Unit tests for the Python client library.
These tests verify the core functionality of routes, components, and the Server class.
"""
import pytest
from drafter import Server, route, Page, TextBox, Button, Text, Table
from drafter.response import Response
from drafter.routes import Router


class TestRouter:
    """Test suite for the Router class."""

    def test_router_initialization(self):
        """Test that a Router can be initialized."""
        router = Router()
        assert router is not None
        assert router.routes == {}

    def test_add_route(self):
        """Test adding a route to the router."""
        router = Router()
        
        def test_func():
            return "test"
        
        router.add_route("test_route", test_func)
        assert "test_route" in router.routes
        assert router.routes["test_route"] == test_func

    def test_get_route(self):
        """Test retrieving a route from the router."""
        router = Router()
        
        def test_func():
            return "test"
        
        router.add_route("test_route", test_func)
        retrieved = router.get_route("test_route")
        assert retrieved == test_func

    def test_get_nonexistent_route(self):
        """Test retrieving a route that doesn't exist."""
        router = Router()
        assert router.get_route("nonexistent") is None


class TestServer:
    """Test suite for the Server class."""

    def test_server_initialization(self):
        """Test that a Server can be initialized."""
        server = Server(custom_name="TEST_SERVER")
        assert server is not None
        assert server.custom_name == "TEST_SERVER"
        assert server.state is None

    def test_server_has_router(self):
        """Test that a Server has a router."""
        server = Server(custom_name="TEST_SERVER")
        assert hasattr(server, "router")
        assert isinstance(server.router, Router)

    def test_server_visit_with_route(self):
        """Test visiting a route on the server."""
        server = Server(custom_name="TEST_SERVER")
        
        @route("index", server=server)
        def index(state):
            return Page(state, ["Test page"])
        
        response = server.visit("index")
        assert isinstance(response, Response)
        assert isinstance(response.page, Page)
        assert response.page.content == ["Test page"]

    def test_server_visit_nonexistent_route(self):
        """Test visiting a route that doesn't exist."""
        server = Server(custom_name="TEST_SERVER")
        
        with pytest.raises(ValueError, match="No route found"):
            server.visit("nonexistent")

    def test_server_state_management(self):
        """Test that server state is maintained."""
        server = Server(custom_name="TEST_SERVER")
        server.state = {"count": 0}
        
        @route("increment", server=server)
        def increment(state):
            state["count"] += 1
            return Page(state, [f"Count: {state['count']}"])
        
        response = server.visit("increment")
        assert server.state["count"] == 1
        assert "Count: 1" in response.page.content[0]

    def test_server_visit_with_arguments(self):
        """Test visiting a route with additional arguments."""
        server = Server(custom_name="TEST_SERVER")
        
        @route("greet", server=server)
        def greet(state, name):
            return Page(state, [f"Hello, {name}!"])
        
        response = server.visit("greet", "Alice")
        assert "Hello, Alice!" in response.page.content[0]


class TestRouteDecorator:
    """Test suite for the route decorator."""

    def test_route_decorator_basic(self):
        """Test basic route decorator usage."""
        server = Server(custom_name="TEST_SERVER")
        
        @route("index", server=server)
        def index(state):
            return Page(state, ["Index page"])
        
        assert "index" in server.router.routes
        assert server.router.routes["index"] == index

    def test_route_decorator_preserves_function(self):
        """Test that route decorator preserves the original function."""
        server = Server(custom_name="TEST_SERVER")
        
        @route("test", server=server)
        def test_func(state):
            return Page(state, ["Test"])
        
        # Function should still be callable
        result = test_func(None)
        assert isinstance(result, Page)


class TestPage:
    """Test suite for the Page class."""

    def test_page_with_state_and_content(self):
        """Test creating a Page with state and content."""
        state = {"key": "value"}
        content = ["Hello, world!"]
        page = Page(state, content)
        
        assert page.state == state
        assert page.content == content

    def test_page_with_only_content(self):
        """Test creating a Page with only content (state defaults to None)."""
        content = ["Hello, world!"]
        page = Page(content)
        
        assert page.state is None
        assert page.content == content

    def test_page_converts_single_string_to_list(self):
        """Test that a single string is converted to a list."""
        page = Page("Hello, world!")
        assert page.content == ["Hello, world!"]

    def test_page_with_components(self):
        """Test creating a Page with component objects."""
        content = [
            "Welcome!",
            TextBox("username"),
            Button("Submit", lambda s: Page(s, ["Submitted!"]))
        ]
        page = Page(None, content)
        
        assert len(page.content) == 3
        assert isinstance(page.content[1], TextBox)
        assert isinstance(page.content[2], Button)

    def test_page_rejects_invalid_content_type(self):
        """Test that Page raises ValueError for invalid content types."""
        with pytest.raises(ValueError, match="must be a list"):
            Page(None, 123)

    def test_page_rejects_invalid_content_item(self):
        """Test that Page raises ValueError for invalid items in content list."""
        with pytest.raises(ValueError, match="must be a list of strings or components"):
            Page(None, ["Valid string", 123])


class TestComponents:
    """Test suite for component classes."""

    def test_text_component(self):
        """Test creating a Text component."""
        text = Text("Hello, world!")
        assert text is not None
        assert "Hello, world!" in str(text)

    def test_textbox_component(self):
        """Test creating a TextBox component."""
        textbox = TextBox("username")
        assert textbox is not None
        assert textbox.name == "username"

    def test_textbox_with_default_value(self):
        """Test creating a TextBox with a default value."""
        textbox = TextBox("username", "default_user")
        assert textbox.name == "username"
        assert textbox.default_value == "default_user"

    def test_button_component(self):
        """Test creating a Button component."""
        def on_click(state):
            return Page(state, ["Clicked!"])
        
        button = Button("Click me", on_click)
        assert button is not None
        assert button.text == "Click me"
        assert button.url == on_click

    def test_table_component(self):
        """Test creating a Table component."""
        data = [["A", "B"], ["C", "D"]]
        table = Table(data)
        assert table is not None
        assert table.rows == data

    def test_textbox_name_validation(self):
        """Test that TextBox validates parameter names."""
        # Valid names
        TextBox("valid_name")
        TextBox("_valid")
        TextBox("valid123")
        
        # Invalid names should raise ValueError
        with pytest.raises(ValueError):
            TextBox("invalid name")  # space
        
        with pytest.raises(ValueError):
            TextBox("123invalid")  # starts with digit
        
        with pytest.raises(ValueError):
            TextBox("")  # empty string


class TestResponse:
    """Test suite for the Response class."""

    def test_response_creation(self):
        """Test creating a Response."""
        page = Page(None, ["Test"])
        response = Response(page)
        
        assert isinstance(response, Response)
        assert response.page == page

    def test_response_preserves_page_data(self):
        """Test that Response preserves page state and content."""
        state = {"count": 5}
        content = ["Count: 5"]
        page = Page(state, content)
        response = Response(page)
        
        assert response.page.state == state
        assert response.page.content == content
