"""Tests for state snapshots (debug menu Save/Load).

Saving reduces the current state to plain JSON data (dataclasses become
nested field dicts) alongside the last route invocation, inside a
StateSnapshotEvent (which the JS SaveLoadManager stores or downloads);
loading rebuilds the state with the shared converter registry against the
running app's state class, restores it, and then replays the route (order
matters: argument preparation reads the current state). The JS half of the
round-trip is covered by js/src/__tests__/debug-saveload.test.tsx.
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

from drafter.bridge.bridger import build_server_hooks
from drafter.bridge.client_bridge import ClientBridge
from drafter.bridge.snapshot import (
    deserialize_state_snapshot,
    serialize_state_snapshot,
)
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import (
    get_main_event_bus,
    get_main_server,
    set_main_server,
)
from drafter.data.request import Request


@dataclass
class Inventory:
    """Nested dataclass to prove recursive reconstruction works."""

    items: list[str]
    capacity: int


@dataclass
class GameState:
    """Module-level so get_type_hints can resolve it during conversion."""

    score: int
    name: str
    inventory: Inventory | None = None


@pytest.fixture
def fresh_server():
    """Install a throwaway main server so tests never mutate a shared one."""
    previous = get_main_server()
    server = ClientServer("SNAPSHOT_TEST_SERVER")
    set_main_server(server)
    yield server
    set_main_server(previous)


@pytest.fixture
def captured_events(fresh_server):
    """Capture all telemetry published during a test.

    The main event bus belongs to the current server, so this depends on
    fresh_server to subscribe to the bus the handlers will publish on.
    """
    events = []
    bus = get_main_event_bus()
    subscription = bus.subscribe("*", events.append)
    yield events
    bus.unsubscribe(subscription)


def events_of_type(events, kind):
    return [event for event in events if event.kind == kind]


class TestSerializeSnapshot:
    def test_state_reduces_to_plain_json_data(self):
        state = GameState(score=42, name="Ada")

        event = serialize_state_snapshot(
            state, "guess", {"answer": 4}, "save", "slot-3", "My Site"
        )

        assert event is not None
        assert event.kind == "StateSnapshot"
        assert event.route == "guess"
        assert json.loads(event.kwargs_json) == {"answer": 4}
        assert json.loads(event.state_json) == {
            "score": 42,
            "name": "Ada",
            "inventory": None,
        }
        assert event.state_type == "GameState"
        assert event.reason == "save"
        assert event.slot == "slot-3"
        assert event.app_title == "My Site"
        assert event.representation is not None

    def test_round_trip_restores_an_equal_state(self):
        state = GameState(
            score=42, name="Ada", inventory=Inventory(items=["map"], capacity=3)
        )
        event = serialize_state_snapshot(state, "guess", {}, "save", "quick")

        restored = deserialize_state_snapshot(
            event.state_json, GameState(score=0, name="")
        )

        assert restored == state
        assert restored is not state
        assert isinstance(restored.inventory, Inventory)

    def test_primitive_state_round_trips(self):
        event = serialize_state_snapshot(42, "index", {}, "save", "quick")

        assert deserialize_state_snapshot(event.state_json, 0) == 42

    def test_snapshot_event_serializes_to_json(self):
        event = serialize_state_snapshot(
            GameState(score=1, name="Bo"), "index", {}, "download", "quick"
        )

        payload = event.to_json()

        assert payload["kind"] == "StateSnapshot"
        assert payload["reason"] == "download"
        assert payload["state_json"] == event.state_json
        assert payload["state_type"] == "GameState"
        # The whole event must survive JSON encoding (it crosses the bridge).
        json.dumps(payload)

    def test_unencodable_state_reports_error_and_returns_none(self, captured_events):
        event = serialize_state_snapshot(lambda: None, "guess", {}, "save", "quick")

        assert event is None
        assert (
            len(events_of_type(captured_events, "bridge.snapshot_encode_failed")) == 1
        )

    def test_unserializable_kwargs_fall_back_to_empty(self, captured_events):
        event = serialize_state_snapshot(
            GameState(score=1, name="Cy"),
            "guess",
            {"widget": object()},
            "save",
            "quick",
        )

        assert event is not None
        assert event.kwargs_json == "{}"
        assert (
            len(
                events_of_type(
                    captured_events, "bridge.snapshot_kwargs_serialization_failed"
                )
            )
            == 1
        )


class TestDeserializeSnapshot:
    def test_corrupt_payload_raises(self):
        with pytest.raises(Exception):
            deserialize_state_snapshot("this is not json", GameState(score=0, name=""))

    def test_shape_mismatch_raises_a_helpful_error(self):
        # Saved data lacks GameState's required fields (e.g. the code
        # changed shape since the save).
        with pytest.raises(ValueError, match="GameState"):
            deserialize_state_snapshot(
                json.dumps({"totally": "different"}),
                GameState(score=0, name=""),
            )

    def test_without_a_current_state_the_raw_data_is_returned(self):
        assert deserialize_state_snapshot('{"score": 1}', None) == {"score": 1}


def make_bridge_stand_in(server):
    """ClientBridge.save/load_state_snapshot only touch the navigator, the
    site title, and the injected server hooks (built here the same way
    bridger builds them), so a minimal stand-in works."""
    navigator = MagicMock()
    navigator.last_request = None
    hooks = build_server_hooks(server, MagicMock(), MagicMock(), MagicMock())
    return SimpleNamespace(
        navigator=navigator,
        site_title="Test Site",
        hooks=hooks,
        _require_hooks=lambda: hooks,
    )


class TestSaveStateSnapshot:
    def test_publishes_snapshot_of_state_and_last_request(
        self, captured_events, fresh_server
    ):
        fresh_server.state.update(GameState(score=7, name="Dot"))
        bridge = make_bridge_stand_in(fresh_server)
        bridge.navigator.last_request = Request("form", "guess", {"answer": 4}, {}, "")
        event = SimpleNamespace(detail=SimpleNamespace(reason="save", slot="slot-2"))

        ClientBridge.save_state_snapshot(bridge, event)

        published = events_of_type(captured_events, "StateSnapshot")
        assert len(published) == 1
        snapshot = published[0]
        assert snapshot.route == "guess"
        assert json.loads(snapshot.kwargs_json) == {"answer": 4}
        assert snapshot.slot == "slot-2"
        assert snapshot.app_title == "Test Site"
        assert deserialize_state_snapshot(
            snapshot.state_json, fresh_server.state.current
        ) == GameState(score=7, name="Dot")

    def test_defaults_before_any_request(self, captured_events, fresh_server):
        fresh_server.state.update(GameState(score=0, name="Eve"))
        bridge = make_bridge_stand_in(fresh_server)

        ClientBridge.save_state_snapshot(bridge, SimpleNamespace(detail=None))

        published = events_of_type(captured_events, "StateSnapshot")
        assert len(published) == 1
        assert published[0].route == "index"
        assert published[0].reason == "save"
        assert published[0].slot == "quick"


class TestLoadStateSnapshot:
    def make_load_event(self, state, route="guess", kwargs=None):
        state_json = serialize_state_snapshot(
            state, route, {}, "save", "quick"
        ).state_json
        return SimpleNamespace(
            detail=SimpleNamespace(
                state_json=state_json,
                route=route,
                kwargs_json=json.dumps(kwargs or {}),
            )
        )

    def test_restores_state_then_replays_route(self, captured_events, fresh_server):
        fresh_server.state.update(GameState(score=0, name="start"))
        bridge = make_bridge_stand_in(fresh_server)
        event = self.make_load_event(
            GameState(score=99, name="saved"), "guess", {"answer": 4}
        )

        ClientBridge.load_state_snapshot(bridge, event)

        assert fresh_server.state.current == GameState(score=99, name="saved")
        assert len(events_of_type(captured_events, "UpdatedState")) == 1
        bridge.navigator.goto.assert_called_once_with(
            "guess", {"answer": 4}, action="system"
        )

    def test_corrupt_payload_reports_friendly_error(
        self, captured_events, fresh_server
    ):
        fresh_server.state.update(GameState(score=1, name="keep"))
        bridge = make_bridge_stand_in(fresh_server)
        event = SimpleNamespace(
            detail=SimpleNamespace(
                state_json="corrupt!!!", route="guess", kwargs_json="{}"
            )
        )

        ClientBridge.load_state_snapshot(bridge, event)

        # The state is untouched and no navigation happened.
        assert fresh_server.state.current == GameState(score=1, name="keep")
        bridge.navigator.goto.assert_not_called()
        assert len(events_of_type(captured_events, "client.load_snapshot_failed")) == 1

    def test_shape_mismatch_reports_friendly_error(self, captured_events, fresh_server):
        fresh_server.state.update(GameState(score=1, name="keep"))
        bridge = make_bridge_stand_in(fresh_server)
        event = SimpleNamespace(
            detail=SimpleNamespace(
                state_json=json.dumps({"unrelated": True}),
                route="guess",
                kwargs_json="{}",
            )
        )

        ClientBridge.load_state_snapshot(bridge, event)

        assert fresh_server.state.current == GameState(score=1, name="keep")
        bridge.navigator.goto.assert_not_called()
        assert len(events_of_type(captured_events, "client.load_snapshot_failed")) == 1

    def test_missing_payload_reports_error(self, captured_events, fresh_server):
        bridge = make_bridge_stand_in(fresh_server)

        ClientBridge.load_state_snapshot(bridge, SimpleNamespace(detail=None))

        bridge.navigator.goto.assert_not_called()
        assert (
            len(events_of_type(captured_events, "client.load_snapshot_missing_payload"))
            == 1
        )
