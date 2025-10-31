"""
Tests for the Monitor and Telemetry subsystem.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from drafter.client_server import ClientServer
from drafter.data.request import Request
from drafter.data.outcome import Outcome
from drafter.data.errors import DrafterError, DrafterWarning, DrafterInfo
from drafter.payloads import Page
from drafter.monitor import Monitor
from drafter.telemetry import (
    RequestTelemetry,
    ResponseTelemetry,
    OutcomeTelemetry,
    PageVisitTelemetry,
    MonitorSnapshot,
)


def test_monitor_tracks_request():
    """Test that the monitor can track a request."""
    monitor = Monitor()
    request = Request(
        id=1,
        action="navigate",
        url="/index",
        args=[],
        kwargs={},
        event={}
    )
    
    monitor.track_request(request)
    
    assert monitor.current_visit is not None
    assert monitor.current_visit.request.request_id == 1
    assert monitor.current_visit.request.url == "/index"


def test_monitor_tracks_response():
    """Test that the monitor can track a response."""
    server = ClientServer("test")
    
    def index(state):
        return Page(None, ["Test"])
    
    server.add_route("index", index)
    server.start()
    
    request = Request(id=1, action="nav", url="index", args=[], kwargs={}, event={})
    response = server.visit(request)
    
    assert server.monitor.current_visit is not None
    assert server.monitor.current_visit.response is not None
    assert server.monitor.current_visit.response.response_id == response.id


def test_monitor_tracks_outcome():
    """Test that the monitor completes a visit with an outcome."""
    server = ClientServer("test")
    
    def index(state):
        return Page(None, ["Test"])
    
    server.add_route("index", index)
    server.start()
    
    request = Request(id=1, action="nav", url="index", args=[], kwargs={}, event={})
    response = server.visit(request)
    outcome = Outcome(id=1, request_id=1, response_id=response.id, status_code=200, message="ACK")
    
    server.report_outcome(outcome)
    
    assert server.monitor.current_visit is None
    assert len(server.monitor.page_visits) == 1
    assert server.monitor.page_visits[0].outcome is not None


def test_monitor_tracks_errors():
    """Test that the monitor tracks errors."""
    monitor = Monitor()
    error = DrafterError("Test error", "test", "details", "/test", "")
    
    monitor.track_error(error)
    
    assert len(monitor.errors) == 1
    assert monitor.errors[0].message == "Test error"


def test_monitor_generates_debug_html():
    """Test that the monitor can generate debug HTML."""
    server = ClientServer("test")
    
    def index(state):
        return Page(None, ["Test"])
    
    server.add_route("index", index)
    server.start(initial_state={"count": 0})
    
    # Make a request
    request = Request(id=1, action="nav", url="index", args=[], kwargs={}, event={})
    response = server.visit(request)
    outcome = Outcome(id=1, request_id=1, response_id=response.id, status_code=200, message="ACK")
    server.report_outcome(outcome)
    
    # Generate debug HTML
    debug_html = server.monitor.generate_debug_html(
        current_state=server.state.current,
        initial_state=server.state.initial,
        routes=server.router.routes,
        server_config=server._get_config_dict()
    )
    
    assert len(debug_html) > 0
    assert "drafter-debug-panel" in debug_html
    assert "Debug Monitor" in debug_html
    assert "<style>" in debug_html
    assert "<script>" in debug_html


def test_monitor_handles_errors_gracefully():
    """Test that the monitor doesn't crash when generating debug HTML fails."""
    monitor = Monitor()
    
    # Even with minimal data, should return some HTML
    debug_html = monitor.generate_debug_html()
    
    assert debug_html is not None
    assert isinstance(debug_html, str)


def test_monitor_snapshot():
    """Test that the monitor can create a snapshot."""
    server = ClientServer("test")
    
    def index(state):
        return Page(None, ["Test"])
    
    server.add_route("index", index)
    server.start(initial_state={"count": 0})
    
    snapshot = server.monitor.get_snapshot(
        current_state=server.state.current,
        initial_state=server.state.initial,
        routes=server.router.routes,
        server_config=server._get_config_dict()
    )
    
    assert isinstance(snapshot, MonitorSnapshot)
    assert snapshot.current_state == {"count": 0}
    assert "index" in snapshot.routes


def test_debug_channel_in_response():
    """Test that responses include the debug channel when enabled."""
    server = ClientServer("test")
    server.configuration.debug_enabled = True
    
    def index(state):
        return Page(None, ["Test"])
    
    server.add_route("index", index)
    server.start()
    
    request = Request(id=1, action="nav", url="index", args=[], kwargs={}, event={})
    response = server.visit(request)
    
    assert "debug" in response.channels
    assert len(response.channels["debug"].messages) > 0
    assert response.channels["debug"].messages[0].kind == "html"


def test_monitor_disabled():
    """Test that the monitor can be disabled."""
    server = ClientServer("test")
    server.monitor.enabled = False
    
    def index(state):
        return Page(None, ["Test"])
    
    server.add_route("index", index)
    server.start()
    
    request = Request(id=1, action="nav", url="index", args=[], kwargs={}, event={})
    response = server.visit(request)
    
    assert server.monitor.current_visit is None
    assert len(server.monitor.page_visits) == 0


if __name__ == "__main__":
    # Run all tests
    test_functions = [
        test_monitor_tracks_request,
        test_monitor_tracks_response,
        test_monitor_tracks_outcome,
        test_monitor_tracks_errors,
        test_monitor_generates_debug_html,
        test_monitor_handles_errors_gracefully,
        test_monitor_snapshot,
        test_debug_channel_in_response,
        test_monitor_disabled,
    ]
    
    print("Running Monitor and Telemetry tests...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✅ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Passed: {passed}/{len(test_functions)}")
    if failed > 0:
        print(f"Failed: {failed}/{len(test_functions)}")
        sys.exit(1)
    else:
        print("All tests passed! ✅")
