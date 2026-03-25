"""
Comprehensive tests for the ClientServer class.

Tests cover initialization, configuration, routing, request processing,
state management, error handling, and server lifecycle.
"""

import pytest
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock, patch

from drafter.client_server.client_server import ClientServer
from drafter.client_server.errors import VisitError
from drafter.data.request import Request
from drafter.data.response import Response
from drafter.payloads.kinds.page import Page
from drafter.payloads.kinds.fragment import Fragment
from drafter.payloads.kinds.redirect import Redirect
from drafter.payloads.kinds.update import Update
from drafter.payloads.kinds.error_page import ErrorPage, SimpleErrorPage
from drafter.payloads.target import Target, DEFAULT_BODY_TARGET
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.monitor.events.errors import DrafterError


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def server():
    """Create a fresh ClientServer instance for each test."""
    return ClientServer("test_server")


@pytest.fixture
def started_server():
    """Create and start a ClientServer instance."""
    server = ClientServer("test_server")
    # Configure the server before starting
    server.do_configuration()
    server.do_start()
    return server


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return Request(
        id=1,
        action="submit",
        url="test_route",
        kwargs={"arg1": "value1"},
        event={},
        dom_id="test-button"
    )


# ============================================================================
# INITIALIZATION AND PHASES
# ============================================================================


class TestInitialization:
    """Tests for ClientServer initialization."""

    def test_server_creation(self, server):
        """Test that a server is created with correct initial state."""
        assert server.custom_name == "test_server"
        assert server.phase == "initialized"
        assert not server.started
        assert server.response_count == 0
        assert isinstance(server.state, SiteState)
        assert server.router is not None
        assert server.site is not None

    def test_event_bus_created(self, server):
        """Test that event bus is initialized."""
        assert server.event_bus is not None

    def test_default_configuration_created(self, server):
        """Test that default configuration is initialized."""
        assert isinstance(server.get_default_configuration(), ClientServerConfiguration)

    def test_phase_transitions(self, server):
        """Test that server phases transition correctly."""
        assert server.phase == "initialized"
        server.transition("starting")
        assert server.phase == "starting"
        server.transition("started")
        assert server.phase == "started"


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================


class TestConfiguration:
    """Tests for configuration management."""

    def test_get_default_configuration(self, server: ClientServer):
        """Test retrieving default configuration."""
        config = server.get_default_configuration()
        assert isinstance(config, ClientServerConfiguration)

    def test_process_dynamic_configuration(self, server):
        """Test processing dynamic configuration."""
        server.reconfigure(in_debug_mode=True)
        config = server.process_dynamic_configuration()
        assert config.in_debug_mode is True

    def test_reconfigure_setting(self, started_server: ClientServer):
        """Test reconfiguring a single setting."""
        started_server.reconfigure(in_debug_mode=True)
        assert started_server.get_config_setting("in_debug_mode") is True

    def test_reconfigure_with_update_default(self, started_server: ClientServer):
        """Test reconfiguring with update_default flag."""
        started_server.reconfigure(update_default=True, in_debug_mode=True)
        assert started_server.get_config_setting("in_debug_mode") is True
        assert started_server.get_default_configuration().in_debug_mode is True

    def test_reconfigure_flip(self, started_server: ClientServer):
        """Test flipping a boolean configuration setting."""
        original = started_server.get_config_setting("in_debug_mode")
        started_server.reconfigure_flip("in_debug_mode")
        assert started_server.get_config_setting("in_debug_mode") is not original

    def test_get_config_setting_before_start(self, server: ClientServer):
        """Test getting config settings before server starts."""
        value = server.get_config_setting("in_debug_mode")
        assert isinstance(value, bool)

    def test_do_configuration(self, server: ClientServer):
        """Test do_configuration method."""
        result = server.do_configuration()
        assert server.phase == "configuring"


# ============================================================================
# SERVER LIFECYCLE
# ============================================================================


class TestServerLifecycle:
    """Tests for server start, stop, and reset."""

    def test_server_start(self, server: ClientServer):
        """Test starting the server."""
        server.do_configuration()
        server.do_start()
        assert server.phase == "started"
        assert server.started is True

    def test_server_start_with_initial_state(self, server: ClientServer):
        """Test starting server with initial state."""
        initial_state = {"count": 0}
        server.do_configuration()
        server.do_start(initial_state=initial_state)
        assert server.state.current == initial_state

    def test_system_routes_registered_on_start(self, server: ClientServer):
        """Test that system routes are registered when server starts."""
        server.do_configuration()
        server.do_start()
        # System routes like --reset, --about should be registered
        assert server.router.has_route("--reset")

    def test_server_reset(self, started_server: ClientServer):
        """Test resetting the server."""
        # Add some state
        started_server.state.update({"test": "data"})
        started_server.response_count = 5
        
        assert started_server.state.current == {"test": "data"}
        
        started_server.state.update({"test": "more_data"})
        
        assert started_server.state.current == {"test": "more_data"}
        
        # Reset
        started_server.reset()
        
        # Verify reset
        assert started_server.response_count == 0
        assert started_server.state.current == {"test": "data"}

    def test_finish_visit_transitions_to_idle(self, started_server: ClientServer):
        """Test that finish_visit transitions to idle phase."""
        started_server.do_finish_visit()
        assert started_server.phase == "idle"


# ============================================================================
# ROUTE MANAGEMENT
# ============================================================================


class TestRouteManagement:
    """Tests for route registration and retrieval."""

    def test_add_route(self, server: ClientServer):
        """Test adding a route."""
        def test_handler():
            return Page(None, ["Test"])
        
        server.add_route("test", test_handler)
        assert server.router.has_route("test")

    def test_get_route_success(self, started_server: ClientServer, sample_request: Request):
        """Test retrieving an existing route."""
        def test_handler():
            return Page(None, ["Test"])
        
        started_server.add_route("test_route", test_handler)
        route_func = started_server.get_route(sample_request)
        assert route_func == test_handler

    def test_get_route_not_found(self, started_server: ClientServer):
        """Test getting a non-existent route raises error."""
        request = Request(1, "click", "nonexistent", {}, {}, "")
        with pytest.raises(VisitError) as exc_info:
            started_server.get_route(request)
        assert exc_info.value.status_code == 404


# ============================================================================
# REQUEST PROCESSING
# ============================================================================


class TestRequestProcessing:
    """Tests for request processing pipeline."""

    def test_do_visit_success(self, started_server: ClientServer):
        """Test successful request visit."""
        def test_handler():
            return Page(None, ["Test Content"])
        
        started_server.add_route("test", test_handler)
        request = Request(1, "click", "test", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert isinstance(response, Response)
        assert response.request_id == request.id
        assert response.status_code == 200

    def test_do_visit_with_state_update(self, started_server: ClientServer):
        """Test visit that updates state."""
        def test_handler():
            return Page({"count": 1}, ["Updated"])
        
        started_server.add_route("test", test_handler)
        request = Request(1, "click", "test", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert started_server.state.current == {"count": 1}
        assert response.status_code == 200

    def test_do_visit_with_arguments(self, started_server: ClientServer):
        """Test visit with route arguments."""
        def test_handler(name: str):
            return Page(None, [f"Hello {name}"])
        
        started_server.add_route("greet", test_handler)
        request = Request(1, "submit", "greet", {"name": "World"}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert response.status_code == 200
        assert "Hello World" in response.body

    def test_execute_route(self, started_server: ClientServer):
        """Test executing a route function."""
        def test_handler(x: int, y: int):
            return Page(None, [f"Sum: {x + y}"])
        
        started_server.add_route("add", test_handler)
        request = Request(1, "submit", "add", {"x": "5", "y": "3"}, {}, "")
        config = started_server.get_current_configuration()
        
        payload, representation = started_server.execute_route(
            test_handler, request, config
        )
        
        assert isinstance(payload, Page)
        assert "8" in payload.content[0]

    def test_start_and_check_timer(self, started_server: ClientServer):
        """Test timing functionality."""
        started_server.start_timer()
        import time
        time.sleep(0.01)  # Sleep for 10ms
        elapsed = started_server.check_timer()
        assert elapsed >= 10  # At least 10ms elapsed

    def test_phase_transitions_during_visit(self, started_server: ClientServer):
        """Test that phases transition correctly during visit."""
        def test_handler():
            # Check phase during execution
            assert started_server.phase == "visiting"
            return Page(None, ["Test"])
        
        started_server.add_route("test", test_handler)
        request = Request(1, "click", "test", {}, {}, "")
        
        started_server.do_visit(request)
        assert started_server.phase == "committing"


# ============================================================================
# PAYLOAD VERIFICATION AND RENDERING
# ============================================================================


class TestPayloadHandling:
    """Tests for payload verification and rendering."""

    def test_verify_payload_page(self, started_server: ClientServer, sample_request: Request):
        """Test verifying a Page payload."""
        payload = Page(None, ["Test"])
        config = started_server.get_current_configuration()
        
        # Should not raise
        started_server.verify_payload(sample_request, payload, config)

    def test_verify_payload_invalid_type(self, started_server: ClientServer, sample_request: Request):
        """Test verifying an invalid payload type."""
        payload = "Not a valid payload"
        config = started_server.get_current_configuration()
        
        with pytest.raises(VisitError) as exc_info:
            started_server.verify_payload(sample_request, payload, config)
        assert exc_info.value.status_code == 501

    def test_render_payload_page(self, started_server: ClientServer, sample_request: Request):
        """Test rendering a Page payload."""
        payload = Page(None, ["<h1>Test</h1>"])
        config = started_server.get_current_configuration()
        
        html = started_server.render_payload(sample_request, payload, config)
        
        assert html is not None
        assert '&lt;h1&gt;Test&lt;/h1&gt;\n' in html

    def test_format_payload(self, started_server: ClientServer, sample_request: Request):
        """Test formatting a payload for history."""
        payload = Page(None, ["Test"])
        config = started_server.get_current_configuration()
        
        formatted = started_server.format_payload(
            sample_request, "test_representation", payload, config
        )
        
        assert isinstance(formatted, str)

    def test_get_messages_from_payload(self, started_server: ClientServer, sample_request: Request):
        """Test extracting messages from payload."""
        payload = Page(None, ["Test"], css=".test { color: red; }")
        config = started_server.get_current_configuration()
        
        messages = started_server.get_messages(sample_request, payload, config)
        
        assert isinstance(messages, list)

    def test_get_target_from_payload(self, started_server: ClientServer, sample_request: Request):
        """Test extracting target from payload."""
        payload = Page(None, ["Test"])
        config = started_server.get_current_configuration()
        
        target = started_server.get_target(sample_request, payload, config)
        
        assert isinstance(target, Target)
        assert target == DEFAULT_BODY_TARGET


# ============================================================================
# STATE MANAGEMENT
# ============================================================================


class TestStateManagement:
    """Tests for state updates and history."""

    def test_handle_state_updates_no_update(self, started_server: ClientServer, sample_request: Request):
        """Test handling payload with no state update."""
        payload = Page(None, ["Test"])
        config = started_server.get_current_configuration()
        
        started_server.handle_state_updates(sample_request, payload, config)
        
        # State should remain None
        assert started_server.state.current is None

    def test_handle_state_updates_with_update(self, started_server: ClientServer, sample_request: Request):
        """Test handling payload with state update."""
        new_state = {"counter": 42}
        payload = Page(new_state, ["Test"])
        config = started_server.get_current_configuration()
        
        started_server.handle_state_updates(sample_request, payload, config)
        
        assert started_server.state.current == new_state

    def test_state_persists_across_requests(self, started_server: ClientServer):
        """Test that state persists across multiple requests."""
        def increment_handler():
            current = started_server.state.current or {"count": 0}
            return Page({"count": current["count"] + 1}, ["Incremented"])
        
        started_server.add_route("increment", increment_handler)
        
        # First request
        request1 = Request(1, "click", "increment", {}, {}, "")
        started_server.do_visit(request1)
        assert started_server.state.current == {"count": 1}
        
        # Second request
        request2 = Request(2, "click", "increment", {}, {}, "")
        started_server.do_visit(request2)
        assert started_server.state.current == {"count": 2}


# ============================================================================
# ERROR HANDLING
# ============================================================================


class TestErrorHandling:
    """Tests for error handling and error responses."""

    def test_make_error_response(self, started_server: ClientServer, sample_request: Request):
        """Test creating an error response."""
        error = DrafterError(
            message="Test error message",
            details="Test details"
        )
        
        response = started_server.make_error_response(sample_request, error, 500)
        
        assert isinstance(response, Response)
        assert response.status_code == 500
        assert len(response.errors) >= 1
        assert response.message == error.message

    def test_visit_error_route_not_found(self, started_server: ClientServer):
        """Test error when route is not found."""
        request = Request(1, "click", "nonexistent", {}, {}, "")
        response = started_server.do_visit(request)
        
        assert response.status_code == 404
        assert len(response.errors) > 0

    def test_visit_error_route_execution_failed(self, started_server: ClientServer):
        """Test error when route execution fails."""
        def failing_handler():
            raise ValueError("Test error")
        
        started_server.add_route("fail", failing_handler)
        request = Request(1, "click", "fail", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert response.status_code == 500
        assert len(response.errors) > 0

    def test_visit_error_invalid_payload(self, started_server: ClientServer):
        """Test error when route returns invalid payload."""
        def invalid_handler():
            return "Not a valid payload"
        
        started_server.add_route("invalid", invalid_handler)
        request = Request(1, "click", "invalid", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert response.status_code == 501
        assert len(response.errors) > 0

    def test_error_page_fallback(self, started_server: ClientServer, sample_request: Request):
        """Test fallback to SimpleErrorPage when ErrorPage fails."""
        with patch.object(started_server.router, 'get_route', return_value=None):
            error = DrafterError(
                message="Test error",
                details="Details"
            )
            
            response = started_server.make_error_response(sample_request, error, 500)
            
            assert isinstance(response.payload, SimpleErrorPage)


# ============================================================================
# RESPONSE CREATION
# ============================================================================


class TestResponseCreation:
    """Tests for response object creation."""

    def test_make_success_response(self, started_server: ClientServer):
        """Test creating a successful response."""
        payload = Page(None, ["Success"])
        
        response = started_server.make_success_response(
            request_id=1,
            url="test",
            body="<p>Success</p>",
            payload=payload,
            messages=[],
            target=None
        )
        
        assert isinstance(response, Response)
        assert response.request_id == 1
        assert response.url == "test"
        assert response.body == "<p>Success</p>"
        assert response.status_code == 200

    def test_response_counter_increments(self, started_server: ClientServer):
        """Test that response counter increments."""
        initial_count = started_server.response_count
        
        payload = Page(None, ["Test"])
        started_server.make_success_response(
            request_id=1,
            url="test",
            body="<p>Test</p>",
            payload=payload,
            messages=[],
            target=None
        )
        
        assert started_server.response_count == initial_count + 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for full request/response cycles."""

    def test_full_cycle_simple_page(self, started_server: ClientServer):
        """Test complete cycle for a simple page request."""
        def home():
            return Page(None, ["<h1>Home</h1>", "<p>Welcome</p>"])
        
        started_server.add_route("home", home)
        request = Request(1, "click", "home", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert response.status_code == 200
        assert '&lt;h1&gt;Home&lt;/h1&gt;\n&lt;p&gt;Welcome&lt;/p&gt;\n' in response.body
        assert '&lt;p&gt;Welcome&lt;/p&gt;' in response.body

    def test_full_cycle_with_state_and_arguments(self, started_server: ClientServer):
        """Test complete cycle with state and arguments."""
        @dataclass
        class Counter:
            count: int
        
        def increment(amount: int):
            current = started_server.state.current or Counter(0)
            new_count = current.count + amount
            return Page(Counter(new_count), [f"Count: {new_count}"])
        
        started_server.add_route("increment", increment)
        request = Request(1, "submit", "increment", {"amount": "5"}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert response.status_code == 200
        assert started_server.state.current.count == 5

    def test_multiple_requests_with_state(self, started_server: ClientServer):
        """Test multiple sequential requests with state changes."""
        @dataclass
        class State:
            items: list
        
        def add_item(item: str):
            current = started_server.state.current or State([])
            new_items = current.items + [item]
            return Page(State(new_items), [f"Items: {', '.join(new_items)}"])
        
        started_server.add_route("add", add_item)
        
        # Add first item
        r1 = Request(1, "submit", "add", {"item": "apple"}, {}, "")
        started_server.do_visit(r1)
        assert len(started_server.state.current.items) == 1
        
        # Add second item
        r2 = Request(2, "submit", "add", {"item": "banana"}, {}, "")
        started_server.do_visit(r2)
        assert len(started_server.state.current.items) == 2
        assert started_server.state.current.items == ["apple", "banana"]


# ============================================================================
# EVENT BUS AND TELEMETRY
# ============================================================================


class TestEventBusAndTelemetry:
    """Tests for event bus and telemetry."""

    def test_event_listener_registration(self, server: ClientServer):
        """Test registering an event listener."""
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        server.do_listen_for_events(handler)
        
        # Events should be processed
        assert len(events_received) > 0

    def test_current_request_id(self, started_server: ClientServer):
        """Test getting current request ID."""
        # No request being processed
        assert started_server.get_current_request_id() is None
        
        # This would require deeper integration testing with request scope


# ============================================================================
# RENDERING AND SITE
# ============================================================================


class TestRenderingAndSite:
    """Tests for site rendering."""

    def test_do_render(self, server: ClientServer):
        """Test rendering the initial site."""
        result = server.do_render()
        
        assert server.phase == "rendering"
        assert hasattr(result, 'site_html')

    def test_precompile_server(self, server: ClientServer):
        """Test precompiling server for faster loading."""
        def index():
            return Page(None, ["<h1>Index</h1>"])
        
        server.add_route("index", index)
        
        server.do_configuration()
        
        body, headers = server.precompile_server(initial_state=None)
        
        assert isinstance(body, str)
        assert len(body) > 0


# ============================================================================
# EDGE CASES AND SPECIAL SCENARIOS
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_route_with_state_injection(self, started_server: ClientServer):
        """Test route that receives state as parameter."""
        def handler_with_state(state):
            current_value = state if state is not None else 0
            return Page(current_value + 1, [f"Value: {current_value + 1}"])
        
        started_server.add_route("with_state", handler_with_state)
        request = Request(1, "click", "with_state", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert response.status_code == 200

    def test_empty_body_response(self, started_server: ClientServer):
        """Test handling responses with no body content."""
        def empty_handler():
            return Update({"status": "updated"})
        
        started_server.add_route("update", empty_handler)
        request = Request(1, "click", "update", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        # Update payloads may not have body
        assert response.status_code == 200

    def test_large_state_object(self, started_server: ClientServer):
        """Test handling large state objects."""
        large_state = {"items": list(range(1000))}
        
        def large_state_handler():
            return Page(large_state, ["Large state"])
        
        started_server.add_route("large", large_state_handler)
        request = Request(1, "click", "large", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert response.status_code == 200
        assert started_server.state.current == large_state

    def test_unicode_content(self, started_server: ClientServer):
        """Test handling unicode content."""
        def unicode_handler():
            return Page(None, ["Hello 世界 🌍"])
        
        started_server.add_route("unicode", unicode_handler)
        request = Request(1, "click", "unicode", {}, {}, "")
        
        response = started_server.do_visit(request)
        
        assert response.status_code == 200
        assert "🌍" in response.body

    def test_concurrent_response_counter(self, started_server: ClientServer):
        """Test response counter maintains uniqueness."""
        responses = []
        
        def simple_handler():
            return Page(None, ["Test"])
        
        started_server.add_route("simple", simple_handler)
        
        for i in range(5):
            request = Request(i, "click", "simple", {}, {}, "")
            response = started_server.do_visit(request)
            responses.append(response)
        
        # All response IDs should be unique
        response_ids = [r.id for r in responses]
        assert len(response_ids) == len(set(response_ids))
