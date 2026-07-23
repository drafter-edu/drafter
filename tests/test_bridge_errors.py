"""Tests for Phase 3: bridge runtime error unification."""

import sys
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.error_handling import (
    raise_bridge_system_error,
    report_bridge_error,
    report_bridge_warning,
)
from drafter.bridge.history import BrowserHistory
from drafter.bridge.navigation import NavigationController
from drafter.client_server.commands import get_main_event_bus
from drafter.data.errors import CATEGORY_BRIDGE, STATUS_ERROR, ErrorDetails
from drafter.data.request import Request
from drafter.data.response import Response


@pytest.fixture
def captured_events():
    """Capture all telemetry published to the main event bus during a test."""
    events = []
    bus = get_main_event_bus()
    subscription = bus.subscribe("*", events.append)
    yield events
    bus.unsubscribe(subscription)


def events_of_type(events, kind):
    return [event for event in events if event.kind == kind]


# ============================================================================
# REPORT HELPERS
# ============================================================================


class TestBridgeReporting:
    def test_report_bridge_error_is_envelope_first(self, captured_events):
        result = report_bridge_error(
            "bridge.test_failure",
            "Something broke",
            "tests.bridge",
            "details",
            exception=ValueError("bad"),
            request_id=5,
            dom_id="el-1",
            route="index",
            phase="channel_execution",
        )
        assert isinstance(result, ErrorDetails)
        envelope = result
        assert envelope.id == "bridge.test_failure"
        assert envelope.category == CATEGORY_BRIDGE
        assert envelope.severity == "error"
        assert envelope.context.phase == "channel_execution"
        assert envelope.context.request_id == 5
        assert envelope.context.dom_id == "el-1"
        assert envelope.status_code == STATUS_ERROR

        matching = events_of_type(captured_events, "bridge.test_failure")
        assert len(matching) == 1
        event = matching[0]
        assert event.metadata.level == "error"
        assert event.correlation.request_id == 5
        assert event.correlation.dom_id == "el-1"
        assert event.correlation.route == "index"

    def test_report_bridge_warning_severity(self, captured_events):
        result = report_bridge_warning(
            "bridge.test_degradation",
            "Fell back to default",
            "tests.bridge",
            "details",
            phase="navigation",
        )
        assert isinstance(result, ErrorDetails)
        assert result.severity == "warning"
        matching = events_of_type(captured_events, "bridge.test_degradation")
        assert len(matching) == 1
        assert matching[0].metadata.level == "warning"

    def test_raise_bridge_system_error_unrecoverable(self, captured_events):
        with pytest.raises(RuntimeError, match="Fatal bridge issue"):
            raise_bridge_system_error(
                "bridge.test_fatal",
                "Fatal bridge issue",
                "tests.bridge",
                "details",
                phase="setup",
            )
        matching = events_of_type(captured_events, "bridge.test_fatal")
        assert len(matching) == 1
        assert matching[0].error.recoverable is False
        assert matching[0].error.context.phase == "setup"


# ============================================================================
# REDIRECT LOOPS
# ============================================================================


class FakeRedirectPayload:
    """Minimal payload that always redirects to the same route."""

    def __init__(self, route="looper"):
        self.route = route

    def is_redirect(self):
        return True

    def get_redirect(self):
        return self.route, {}

    def __repr__(self):
        return f"FakeRedirectPayload({self.route})"


def make_redirect_response(payload):
    return Response(
        id=11,
        request_id=10,
        payload=payload,
        url="looper",
    )


class TestRedirectLoop:
    def test_redirect_loop_aborts_deterministically(self, captured_events):
        navigator = NavigationController(MagicMock())
        response = make_redirect_response(FakeRedirectPayload())
        callback_calls = []

        def looping_callback(request):
            callback_calls.append(request)
            # Simulate the server responding with the same redirect again.
            navigator.handle_redirect(response, looping_callback)

        navigator.handle_redirect(response, looping_callback)

        # The chain is aborted at the first repeat: exactly one follow-up.
        assert len(callback_calls) == 1
        assert callback_calls[0].url == "looper"

        matching = events_of_type(captured_events, "bridge.redirect_loop_detected")
        assert len(matching) == 1
        event = matching[0]
        assert event.metadata.level == "error"
        assert event.correlation.request_id == 10
        assert event.correlation.response_id == 11
        assert event.correlation.route == "looper"
        assert event.error.context.phase == "navigation"
        # Stack unwound cleanly: a later redirect is allowed again.
        assert navigator.redirect_loop_stack == []

    def test_redirect_without_loop_reports_nothing(self, captured_events):
        navigator = NavigationController(MagicMock())
        response = make_redirect_response(FakeRedirectPayload())
        callback_calls = []

        navigator.handle_redirect(response, callback_calls.append)

        assert len(callback_calls) == 1
        assert events_of_type(captured_events, "bridge.redirect_loop_detected") == []
        assert navigator.redirect_loop_stack == []

    def test_redirect_loop_is_repeatable(self, captured_events):
        """Loop detection behaves identically across repeated navigations."""
        navigator = NavigationController(MagicMock())
        response = make_redirect_response(FakeRedirectPayload())

        def looping_callback(request):
            navigator.handle_redirect(response, looping_callback)

        navigator.handle_redirect(response, looping_callback)
        navigator.handle_redirect(response, looping_callback)

        matching = events_of_type(captured_events, "bridge.redirect_loop_detected")
        assert len(matching) == 2


# ============================================================================
# BROWSER HISTORY
# ============================================================================


class TestBrowserHistory:
    def test_unserializable_kwargs_reports_warning(self, captured_events):
        runtime = MagicMock()
        history = BrowserHistory(runtime)
        request = Request("click", "route", {"bad": object()}, {}, "")

        history.add_to_history(request)

        matching = events_of_type(
            captured_events, "bridge.history_kwargs_serialization_failed"
        )
        assert len(matching) == 1
        event = matching[0]
        assert event.metadata.level == "warning"
        assert event.correlation.request_id == request.id
        assert event.correlation.route == "route"
        assert event.error.context.phase == "navigation"
        # Fallback still records history with empty kwargs.
        runtime.history_push_state.assert_called_once()
        state = runtime.history_push_state.call_args[0][0]
        assert state["kwargs"] == "{}"

    def test_serializable_kwargs_reports_nothing(self, captured_events):
        runtime = MagicMock()
        history = BrowserHistory(runtime)
        request = Request("click", "route", {"fine": 1}, {}, "")

        history.add_to_history(request)

        assert (
            events_of_type(
                captured_events, "bridge.history_kwargs_serialization_failed"
            )
            == []
        )
        state = runtime.history_push_state.call_args[0][0]
        assert state["kwargs"] == '{"fine": 1}'
