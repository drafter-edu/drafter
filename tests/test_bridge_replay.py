"""Tests for request replay (debug menu "Replay Route" / history "Revisit").

The NavigationController records dispatched Requests (last_request plus a
bounded request_log) so the debug UI can replay them by dispatching the
drafter-replay-route / drafter-replay-request window events; telemetry only
carries a repr of a request's kwargs, so replays must come from these
Python-side Request objects.
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.client_bridge import ClientBridge
from drafter.bridge.navigation import NavigationController
from drafter.client_server.commands import get_main_event_bus
from drafter.data.request import Request


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


def make_navigator():
    """A NavigationController with a recording navigation function and a
    history that does not touch the (mocked) browser."""
    navigator = NavigationController(MagicMock())
    navigator.history = MagicMock()
    dispatched = []

    def navigation_func(request):
        dispatched.append(request)
        return SimpleNamespace(url=request.url)

    navigator.set_navigation_func(navigation_func)
    return navigator, dispatched


class TestRecordRequest:
    def test_navigate_records_last_request_and_log(self):
        navigator, dispatched = make_navigator()
        request = Request("link", "guess", {"answer": 4}, {}, "")

        navigator.navigate(request)

        assert navigator.last_request is request
        assert navigator.request_log[request.id] is request
        assert dispatched == [request]

    def test_request_log_is_bounded(self):
        navigator, _ = make_navigator()

        requests = [
            Request("link", f"route{i}", {}, {}, "")
            for i in range(NavigationController.REQUEST_LOG_LIMIT + 5)
        ]
        for request in requests:
            navigator.navigate(request)

        assert len(navigator.request_log) == NavigationController.REQUEST_LOG_LIMIT
        # The oldest entries were evicted; the newest are all present.
        assert requests[0].id not in navigator.request_log
        assert requests[-1].id in navigator.request_log


class TestReplayLast:
    def test_replays_route_and_arguments_without_history(self, captured_events):
        navigator, dispatched = make_navigator()
        original = Request(
            "form", "guess", {"answer": 4}, {}, "dom-1", button_pressed="Go"
        )
        navigator.navigate(original)
        navigator.history.add_to_history.reset_mock()

        response = navigator.replay_last()

        assert response.url == "guess"
        assert len(dispatched) == 2
        replayed = dispatched[-1]
        # A fresh Request (new id) with the same invocation details.
        assert replayed is not original
        assert replayed.id != original.id
        assert replayed.url == original.url
        assert replayed.kwargs == original.kwargs
        assert replayed.kwargs is not original.kwargs
        assert replayed.action == original.action
        assert replayed.button_pressed == original.button_pressed
        # Replays never add browser-history entries.
        navigator.history.add_to_history.assert_not_called()
        assert not events_of_type(captured_events, "bridge.replay_without_request")

    def test_replay_before_any_request_warns(self, captured_events):
        navigator, dispatched = make_navigator()

        assert navigator.replay_last() is None

        assert dispatched == []
        assert (
            len(events_of_type(captured_events, "bridge.replay_without_request")) == 1
        )

    def test_replay_becomes_the_new_last_request(self):
        navigator, dispatched = make_navigator()
        navigator.navigate(Request("link", "guess", {}, {}, ""))

        navigator.replay_last()

        assert navigator.last_request is dispatched[-1]


class TestReplayById:
    def test_replays_the_matching_logged_request(self):
        navigator, dispatched = make_navigator()
        first = Request("link", "first", {"n": 1}, {}, "")
        second = Request("link", "second", {"n": 2}, {}, "")
        navigator.navigate(first)
        navigator.navigate(second)

        navigator.replay_by_id(first.id)

        assert dispatched[-1].url == "first"
        assert dispatched[-1].kwargs == {"n": 1}

    def test_unknown_id_warns_and_returns_none(self, captured_events):
        navigator, dispatched = make_navigator()
        navigator.navigate(Request("link", "guess", {}, {}, ""))

        assert navigator.replay_by_id(999999) is None

        assert len(dispatched) == 1
        assert (
            len(events_of_type(captured_events, "bridge.replay_unknown_request")) == 1
        )

    def test_unknown_id_uses_fallback_url_and_kwargs(self, captured_events):
        # After a bridge restart the request_log is empty, but the debug
        # history still knows the url/kwargs from telemetry.
        navigator, dispatched = make_navigator()

        response = navigator.replay_by_id(
            999999, fallback_url="guess", fallback_kwargs={"answer": 4}
        )

        assert response.url == "guess"
        assert dispatched[-1].url == "guess"
        assert dispatched[-1].kwargs == {"answer": 4}
        # No history entry and no error report for the fallback path.
        navigator.history.add_to_history.assert_not_called()
        assert not events_of_type(captured_events, "bridge.replay_unknown_request")


class TestClientBridgeReplayRequest:
    """ClientBridge.replay_request only touches self.navigator, so it can be
    exercised with a minimal stand-in for the bridge."""

    def test_forwards_the_request_id_as_int(self):
        navigator = MagicMock()
        fake_bridge = SimpleNamespace(navigator=navigator)
        event = SimpleNamespace(detail=SimpleNamespace(request_id="17"))

        ClientBridge.replay_request(fake_bridge, event)

        navigator.replay_by_id.assert_called_once_with(
            17, fallback_url=None, fallback_kwargs={}
        )

    def test_forwards_url_and_decoded_kwargs_for_fallback(self):
        navigator = MagicMock()
        fake_bridge = SimpleNamespace(navigator=navigator)
        event = SimpleNamespace(
            detail=SimpleNamespace(
                request_id=17, url="guess", kwargs_json='{"answer": 4}'
            )
        )

        ClientBridge.replay_request(fake_bridge, event)

        navigator.replay_by_id.assert_called_once_with(
            17, fallback_url="guess", fallback_kwargs={"answer": 4}
        )

    def test_bad_kwargs_json_falls_back_to_empty(self):
        navigator = MagicMock()
        fake_bridge = SimpleNamespace(navigator=navigator)
        event = SimpleNamespace(
            detail=SimpleNamespace(request_id=17, url="guess", kwargs_json="not json")
        )

        ClientBridge.replay_request(fake_bridge, event)

        navigator.replay_by_id.assert_called_once_with(
            17, fallback_url="guess", fallback_kwargs={}
        )

    def test_missing_detail_reports_instead_of_raising(self, captured_events):
        navigator = MagicMock()
        fake_bridge = SimpleNamespace(navigator=navigator)

        ClientBridge.replay_request(fake_bridge, SimpleNamespace(detail=None))

        navigator.replay_by_id.assert_not_called()
        assert (
            len(events_of_type(captured_events, "client.replay_request_missing_id"))
            == 1
        )
