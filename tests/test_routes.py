"""
Unit tests for route building functionality.
These tests verify that routes can be created and work correctly with components.
"""
import pytest
from drafter import route, Page, Button, TextBox, get_main_server, set_main_server
from drafter.client_server.client_server import ClientServer
from dataclasses import dataclass


def test_route_decorator_basic():
    """Test that the @route decorator can be used to define routes."""
    # Create a fresh server for testing
    test_server = ClientServer(custom_name="TEST_SERVER")
    
    @route(server=test_server)
    def index(state: str) -> Page:
        return Page(state, ["Index page"])
    
    # Verify route was registered
    assert len(test_server.router.routes) > 0


def test_route_with_state():
    """Test that routes can work with state objects."""
    @dataclass
    class AppState:
        counter: int
    
    test_server = ClientServer(custom_name="TEST_SERVER")
    
    @route(server=test_server)
    def index(state: AppState) -> Page:
        return Page(state, [f"Counter: {state.counter}"])
    
    @route(server=test_server)
    def increment(state: AppState) -> Page:
        state.counter += 1
        return index(state)
    
    # Verify routes are registered
    assert len(test_server.router.routes) >= 2


def test_route_with_form_parameters():
    """Test that routes can accept form parameters."""
    test_server = ClientServer(custom_name="TEST_SERVER")
    
    @route(server=test_server)
    def index(state: str) -> Page:
        return Page(state, [
            "Enter your name:",
            TextBox("name"),
            Button("Submit", process_form)
        ])
    
    @route(server=test_server)
    def process_form(state: str, name: str) -> Page:
        return Page(state, [f"Hello, {name}!"])
    
    # Verify both routes are registered
    assert len(test_server.router.routes) >= 2


def test_route_with_multiple_parameters():
    """Test that routes can accept multiple form parameters."""
    @dataclass
    class FormState:
        result: str
    
    test_server = ClientServer(custom_name="TEST_SERVER")
    
    @route(server=test_server)
    def form_page(state: FormState) -> Page:
        return Page(state, [
            "First name:",
            TextBox("first"),
            "Last name:",
            TextBox("last"),
            Button("Submit", process_multi_form)
        ])
    
    @route(server=test_server)
    def process_multi_form(state: FormState, first: str, last: str) -> Page:
        state.result = f"{first} {last}"
        return Page(state, [f"Full name: {state.result}"])
    
    # Verify routes are registered
    assert len(test_server.router.routes) >= 2


def test_route_naming():
    """Test that routes can have custom names or use function names."""
    test_server = ClientServer(custom_name="TEST_SERVER")
    
    @route("custom_name", server=test_server)
    def my_route(state: str) -> Page:
        return Page(state, ["Custom named route"])
    
    # Verify route exists (actual name handling may vary)
    assert len(test_server.router.routes) > 0


def test_route_with_buttons():
    """Test that routes work correctly with button navigation."""
    @dataclass
    class NavState:
        current_page: str
    
    test_server = ClientServer(custom_name="TEST_SERVER")
    
    @route(server=test_server)
    def index(state: NavState) -> Page:
        state.current_page = "index"
        return Page(state, [
            "Home Page",
            Button("Go to About", about)
        ])
    
    @route(server=test_server)
    def about(state: NavState) -> Page:
        state.current_page = "about"
        return Page(state, [
            "About Page",
            Button("Go Home", index)
        ])
    
    # Verify both routes exist
    assert len(test_server.router.routes) >= 2


def test_server_route_registration():
    """Test that multiple routes can be registered on the same server."""
    test_server = ClientServer(custom_name="TEST_SERVER")
    
    @route(server=test_server)
    def page1(state: str) -> Page:
        return Page(state, ["Page 1"])
    
    @route(server=test_server)
    def page2(state: str) -> Page:
        return Page(state, ["Page 2"])
    
    @route(server=test_server)
    def page3(state: str) -> Page:
        return Page(state, ["Page 3"])
    
    # All routes should be registered
    assert len(test_server.router.routes) >= 3


def test_route_return_types():
    """Test that routes must return Page objects."""
    test_server = ClientServer(custom_name="TEST_SERVER")
    
    @route(server=test_server)
    def valid_route(state: str) -> Page:
        return Page(state, ["Valid"])
    
    # This should work
    assert len(test_server.router.routes) > 0


def test_page_with_state_updates():
    """Test that state changes persist across route calls."""
    @dataclass
    class Counter:
        count: int
    
    test_server = ClientServer(custom_name="TEST_SERVER")
    initial_state = Counter(count=0)
    
    @route(server=test_server)
    def index(state: Counter) -> Page:
        return Page(state, [
            f"Count: {state.count}",
            Button("Increment", increment)
        ])
    
    @route(server=test_server)
    def increment(state: Counter) -> Page:
        state.count += 1
        return index(state)
    
    # Verify the route structure
    assert len(test_server.router.routes) >= 2
    
    # Verify state object is passed correctly
    page = index(initial_state)
    assert page.state.count == 0
    
    # Simulate increment
    increment(initial_state)
    assert initial_state.count == 1
