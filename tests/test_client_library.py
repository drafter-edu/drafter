"""
Unit tests for the Python client library that builds routes using components.

These tests verify that the ClientServer properly handles routes, components,
and the history/monitor features.
"""
import pytest
from drafter.client_server.client_server import ClientServer
from drafter.router.routes import Router
from drafter.history.state import SiteState
from drafter.history.pages import VisitedPage
from drafter.monitor.monitor import Monitor
from drafter.payloads import Page
from drafter.components import TextBox, Button, Header, SelectBox, CheckBox
from drafter.data.request import Request


def test_client_server_initialization():
    """Test that ClientServer initializes with proper components"""
    server = ClientServer(custom_name="TEST_SERVER")
    
    assert server.custom_name == "TEST_SERVER"
    assert isinstance(server.router, Router)
    assert isinstance(server.state, SiteState)
    assert isinstance(server.monitor, Monitor)
    assert server.response_count == 0


def test_client_server_has_site():
    """Test that ClientServer has a Site instance"""
    server = ClientServer(custom_name="TEST_SERVER")
    
    assert hasattr(server, 'site')
    assert server.site is not None


def test_router_registration():
    """Test that routes can be registered with the router"""
    server = ClientServer(custom_name="TEST_SERVER")
    
    def test_route(state: str) -> Page:
        return Page(state, ["Test content"])
    
    server.router.add_route("test", test_route)
    
    assert "test" in server.router.routes
    assert server.router.routes["test"] == test_route


def test_page_with_text_box_component():
    """Test creating a Page with TextBox component"""
    page = Page(None, [
        "Enter your name:",
        TextBox("name", ""),
    ])
    
    assert page is not None
    assert len(page.content) == 2
    assert isinstance(page.content[1], TextBox)
    assert page.content[1].name == "name"


def test_page_with_button_component():
    """Test creating a Page with Button component"""
    def handler(state: str) -> Page:
        return Page(state, ["Clicked!"])
    
    page = Page(None, [
        "Click me:",
        Button("Submit", handler),
    ])
    
    assert page is not None
    assert len(page.content) == 2
    assert isinstance(page.content[1], Button)
    assert page.content[1].text == "Submit"


def test_page_with_header_component():
    """Test creating a Page with Header component"""
    page = Page(None, [
        Header("Welcome", level=1),
        "Some text content",
    ])
    
    assert page is not None
    assert isinstance(page.content[0], Header)
    assert page.content[0].body == "Welcome"
    assert page.content[0].level == 1


def test_page_with_select_box_component():
    """Test creating a Page with SelectBox component"""
    page = Page(None, [
        "Choose an option:",
        SelectBox("choice", ["Option 1", "Option 2", "Option 3"], "Option 1"),
    ])
    
    assert page is not None
    assert isinstance(page.content[1], SelectBox)
    assert page.content[1].name == "choice"
    assert len(page.content[1].options) == 3


def test_page_with_checkbox_component():
    """Test creating a Page with CheckBox component"""
    page = Page(None, [
        "Agree to terms:",
        CheckBox("agree", False),
    ])
    
    assert page is not None
    assert isinstance(page.content[1], CheckBox)
    assert page.content[1].name == "agree"
    assert page.content[1].default_value is False


def test_page_with_multiple_components():
    """Test creating a Page with multiple different components"""
    page = Page(None, [
        Header("Form Title", level=2),
        "Enter your information:",
        TextBox("name", ""),
        TextBox("email", ""),
        CheckBox("subscribe", False),
        Button("Submit", lambda state: Page(state, ["Done"])),
    ])
    
    assert page is not None
    assert len(page.content) == 6
    assert isinstance(page.content[0], Header)
    assert isinstance(page.content[2], TextBox)
    assert isinstance(page.content[3], TextBox)
    assert isinstance(page.content[4], CheckBox)
    assert isinstance(page.content[5], Button)


def test_site_state_initialization():
    """Test that SiteState initializes correctly"""
    state = SiteState()
    
    assert state is not None
    assert hasattr(state, 'current')
    assert hasattr(state, 'history')
    assert hasattr(state, 'initial')


def test_monitor_initialization():
    """Test that Monitor initializes correctly"""
    monitor = Monitor()
    
    assert monitor is not None


def test_visited_page_creation():
    """Test creating a VisitedPage for history tracking"""
    def test_func(state):
        return Page(state, ["Test"])
    
    visited = VisitedPage(
        url="test",
        function=test_func,
        arguments="state=None",
        status="processing",
        old_state=None
    )
    
    assert visited.url == "test"
    assert visited.function == test_func
    assert visited.status == "processing"
    assert visited.started is not None
    assert visited.stopped is None


def test_visited_page_update():
    """Test updating a VisitedPage status"""
    def test_func(state):
        return Page(state, ["Test"])
    
    visited = VisitedPage(
        url="test",
        function=test_func,
        arguments="state=None",
        status="processing",
        old_state=None
    )
    
    visited.update("completed")
    assert visited.status == "completed"


def test_visited_page_finish():
    """Test finishing a VisitedPage"""
    def test_func(state):
        return Page(state, ["Test"])
    
    visited = VisitedPage(
        url="test",
        function=test_func,
        arguments="state=None",
        status="processing",
        old_state=None
    )
    
    visited.finish("success")
    assert visited.status == "success"
    assert visited.stopped is not None


def test_component_name_extraction():
    """Test that component names are properly set"""
    textbox = TextBox("user_name", "default")
    assert textbox.name == "user_name"
    
    checkbox = CheckBox("is_active", True)
    assert checkbox.name == "is_active"
    
    selectbox = SelectBox("country", ["USA", "UK"], "USA")
    assert selectbox.name == "country"


def test_button_with_target_route():
    """Test that Button properly stores target route information"""
    def target_route(state):
        return Page(state, ["Target reached"])
    
    button = Button("Go", target_route)
    assert button.text == "Go"
    assert button.url == "target_route"  # Button converts callable to name


def test_page_state_preservation():
    """Test that Page properly stores state information"""
    state = "test_state"
    page = Page(state, ["Content"])
    
    assert page.state == state
    assert len(page.content) == 1
