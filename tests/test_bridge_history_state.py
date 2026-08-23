"""Tests for browser-history time travel (back/forward state restoration).

Each history entry the BrowserHistory pushes carries a JSON snapshot of the
application state as it was before the entry's route ran; on popstate the
NavigationController restores that snapshot (rebuilt against the running
app's state class, like the Save/Load feature) before replaying the route,
so back/forward reproduces the original page instead of re-running the
route against whatever the state has since become. Entries without a usable
snapshot degrade to the old replay behavior.
"""

import json
import sys
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.history import BrowserHistory
from drafter.bridge.navigation import NavigationController
from drafter.bridge.snapshot import encode_state_json
from drafter.client_server.commands import get_main_event_bus
from drafter.data.request import Request


@dataclass
class GameState:
    """Module-level so get_type_hints can resolve it during conversion."""

    score: int
    name: str


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


class StateBox:
    """A stand-in for the server's state slot, exposing hook-style accessors."""

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def pushed_entry(runtime):
    """The state dict of the most recent history_push_state call."""
    return runtime.history_push_state.call_args[0][0]


# ============================================================================
# CAPTURE: snapshots recorded into pushed entries
# ============================================================================


class TestCaptureIntoEntries:
    def test_entry_includes_state_snapshot(self, captured_events):
        runtime = MagicMock()
        history = BrowserHistory(runtime)
        box = StateBox(GameState(score=3, name="Ada"))
        history.set_state_provider(box.get)

        history.add_to_history(Request("link", "shop", {"n": 1}, {}, ""))

        entry = pushed_entry(runtime)
        assert json.loads(entry["state_json"]) == {"score": 3, "name": "Ada"}
        assert entry["kwargs"] == '{"n": 1}'
        assert (
            events_of_type(captured_events, "bridge.history_state_serialization_failed")
            == []
        )

    def test_no_provider_omits_snapshot_without_warning(self, captured_events):
        runtime = MagicMock()
        history = BrowserHistory(runtime)

        history.add_to_history(Request("link", "shop", {}, {}, ""))

        entry = pushed_entry(runtime)
        assert "state_json" not in entry
        assert (
            events_of_type(captured_events, "bridge.history_state_serialization_failed")
            == []
        )

    def test_unencodable_state_warns_and_omits_snapshot(self, captured_events):
        runtime = MagicMock()
        history = BrowserHistory(runtime)
        history.set_state_provider(lambda: object())

        request = Request("link", "shop", {"n": 1}, {}, "")
        history.add_to_history(request)

        entry = pushed_entry(runtime)
        assert "state_json" not in entry
        # The entry itself is still recorded (route + kwargs intact).
        assert entry["url"] == "shop"
        assert entry["kwargs"] == '{"n": 1}'
        matching = events_of_type(
            captured_events, "bridge.history_state_serialization_failed"
        )
        assert len(matching) == 1
        assert matching[0].metadata.level == "warning"
        assert matching[0].correlation.request_id == request.id
        assert matching[0].correlation.route == "shop"

    def test_oversized_state_warns_and_omits_snapshot(self, captured_events):
        runtime = MagicMock()
        history = BrowserHistory(runtime)
        history.MAX_STATE_JSON_LENGTH = 10
        history.set_state_provider(lambda: GameState(score=1, name="A" * 50))

        history.add_to_history(Request("link", "shop", {}, {}, ""))

        assert "state_json" not in pushed_entry(runtime)
        assert (
            len(events_of_type(captured_events, "bridge.history_state_too_large")) == 1
        )


class TestRecordInitialState:
    def test_stamps_startup_state_onto_original_entry(self):
        runtime = MagicMock()
        history = BrowserHistory(runtime)
        history.set_state_provider(lambda: GameState(score=0, name="Ada"))

        history.record_initial_state()

        runtime.history_replace_state.assert_called_once()
        entry = runtime.history_replace_state.call_args[0][0]
        assert json.loads(entry["state_json"]) == {"score": 0, "name": "Ada"}
        assert "request_id" not in entry

    def test_does_nothing_without_a_provider(self):
        runtime = MagicMock()
        history = BrowserHistory(runtime)

        history.record_initial_state()

        runtime.history_replace_state.assert_not_called()


# ============================================================================
# RESTORE: popstate entries restore their snapshot before replaying
# ============================================================================


def make_navigator(box):
    """A NavigationController with recording navigation + state accessors.

    Returns the navigator plus a timeline list interleaving state
    restorations and dispatched requests, to assert restore-before-dispatch
    ordering.
    """
    navigator = NavigationController(MagicMock())
    timeline = []

    def navigation_func(request):
        timeline.append(("dispatch", request))
        return SimpleNamespace(url=request.url)

    def set_state(value):
        box.set(value)
        timeline.append(("restore", value))

    navigator.set_navigation_func(navigation_func)
    navigator.set_state_accessors(box.get, set_state)
    return navigator, timeline


def make_popstate_event(**entry_fields):
    """A popstate event whose entry exposes fields as attributes, the way
    the browser's (JS-proxied) history state does."""
    return SimpleNamespace(state=SimpleNamespace(**entry_fields))


class TestRestoreOnPopstate:
    def test_restores_snapshot_before_replaying_the_route(self, captured_events):
        box = StateBox(GameState(score=99, name="Ada"))
        navigator, timeline = make_navigator(box)
        event = make_popstate_event(
            request_id=5,
            url="shop",
            kwargs='{"n": 2}',
            state_json=encode_state_json(GameState(score=7, name="Babbage")),
        )

        navigator.handle_popstate(event)

        # Snapshot rebuilt against the running state class, then dispatched.
        assert [kind for kind, _ in timeline] == ["restore", "dispatch"]
        assert box.value == GameState(score=7, name="Babbage")
        request = timeline[-1][1]
        assert request.action == "back"
        assert request.url == "shop"
        assert request.kwargs == {"n": 2}
        assert len(events_of_type(captured_events, "UpdatedState")) == 1, (
            "restoring should notify the debug UI of the state change"
        )

    def test_initial_entry_snapshot_restores_without_request_id(self):
        box = StateBox(GameState(score=42, name="Ada"))
        navigator, timeline = make_navigator(box)
        event = make_popstate_event(
            state_json=encode_state_json(GameState(score=0, name="Ada"))
        )

        navigator.handle_popstate(event)

        assert box.value == GameState(score=0, name="Ada")
        assert timeline[-1][1].url == "index"

    def test_unrestorable_snapshot_warns_and_replays_with_current_state(
        self, captured_events
    ):
        box = StateBox(GameState(score=99, name="Ada"))
        navigator, timeline = make_navigator(box)
        event = make_popstate_event(
            request_id=5, url="shop", kwargs="{}", state_json="not json"
        )

        navigator.handle_popstate(event)

        # State untouched; the navigation still happened (plain replay).
        assert box.value == GameState(score=99, name="Ada")
        assert [kind for kind, _ in timeline] == ["dispatch"]
        assert timeline[-1][1].url == "shop"
        matching = events_of_type(
            captured_events, "bridge.history_state_restore_failed"
        )
        assert len(matching) == 1
        assert matching[0].metadata.level == "warning"
        assert matching[0].correlation.route == "shop"

    def test_mismatched_snapshot_shape_warns_and_replays(self, captured_events):
        box = StateBox(GameState(score=99, name="Ada"))
        navigator, timeline = make_navigator(box)
        event = make_popstate_event(
            request_id=5,
            url="shop",
            kwargs="{}",
            state_json=json.dumps({"bogus_field": True}),
        )

        navigator.handle_popstate(event)

        assert box.value == GameState(score=99, name="Ada")
        assert [kind for kind, _ in timeline] == ["dispatch"]
        assert (
            len(events_of_type(captured_events, "bridge.history_state_restore_failed"))
            == 1
        )

    def test_entry_without_snapshot_replays_without_warning(self, captured_events):
        box = StateBox(GameState(score=99, name="Ada"))
        navigator, timeline = make_navigator(box)
        event = make_popstate_event(request_id=5, url="shop", kwargs="{}")

        navigator.handle_popstate(event)

        assert box.value == GameState(score=99, name="Ada")
        assert [kind for kind, _ in timeline] == ["dispatch"]
        assert (
            events_of_type(captured_events, "bridge.history_state_restore_failed") == []
        )

    def test_without_accessors_snapshot_is_ignored(self):
        navigator = NavigationController(MagicMock())
        dispatched = []
        navigator.set_navigation_func(
            lambda request: dispatched.append(request)
            or SimpleNamespace(url=request.url)
        )
        event = make_popstate_event(
            request_id=5,
            url="shop",
            kwargs="{}",
            state_json=encode_state_json(GameState(score=7, name="Babbage")),
        )

        navigator.handle_popstate(event)

        assert dispatched[-1].url == "shop"


# ============================================================================
# END TO END: a push's snapshot round-trips through a popstate
# ============================================================================


class TestTimeTravelRoundTrip:
    def test_back_restores_the_pre_visit_state(self):
        box = StateBox(GameState(score=0, name="Ada"))
        navigator, timeline = make_navigator(box)

        # Visit "shop": the entry captures the pre-visit state (score=0).
        navigator.navigate(Request("link", "shop", {"n": 1}, {}, ""))
        runtime = navigator.history.runtime
        entry = pushed_entry(runtime)
        assert json.loads(entry["state_json"]) == {"score": 0, "name": "Ada"}

        # The route (or later visits) mutate the state.
        box.value = GameState(score=10, name="Ada")

        # Back to the "shop" entry: the browser hands back the pushed entry.
        navigator.handle_popstate(SimpleNamespace(state=SimpleNamespace(**entry)))

        assert box.value == GameState(score=0, name="Ada")
        assert timeline[-1][1].url == "shop"
        assert timeline[-1][1].kwargs == {"n": 1}

    def test_initial_request_stamps_the_original_entry_first(self):
        box = StateBox(GameState(score=0, name="Ada"))
        navigator, timeline = make_navigator(box)
        navigator.history = MagicMock()

        navigator.do_initial_request()

        navigator.history.record_initial_state.assert_called_once()
        assert timeline[-1][1].url == "index"
        # The initial request itself is never pushed onto the stack.
        navigator.history.add_to_history.assert_not_called()
