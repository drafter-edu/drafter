"""Tests for state snapshots (debug menu Save/Load).

Saving reduces the current state to plain JSON data (dataclasses become
nested field dicts) alongside the last route invocation, inside a
StateSnapshotEvent (which the JS SaveLoadManager stores or downloads);
loading rebuilds the state with the shared converter registry against the
running app's state class, restores it, and then replays the route (order
matters: argument preparation reads the current state). The JS half of the
round-trip is covered by js/src/__tests__/debug-saveload.test.tsx.

A snapshot carries two states: the one from after its route ran
(`state_json`) and the one from before (`state_before_json`). Loading
restores the earlier one, so replaying the route arrives at the saved page
instead of one step past it; snapshots saved before the second state
existed are still loaded the old way.
"""

import json
import sys
from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.bridger import build_server_hooks
from drafter.bridge.client_bridge import ClientBridge
from drafter.bridge.navigation import NavigationController
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
from drafter.data.details.snapshot import SNAPSHOT_VERSION
from drafter.data.request import Request
from drafter.payloads.kinds.page import Page


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


@dataclass
class TreeNode:
    """Self-referential dataclass to prove cycles survive the round trip."""

    name: str
    children: list["TreeNode"] = field(default_factory=list)
    parent: "TreeNode | None" = None


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


class TestCircularReferences:
    def test_self_cycle_encodes_with_reference_marker(self):
        node = TreeNode(name="root")
        node.parent = node

        event = serialize_state_snapshot(node, "index", {}, "save", "quick")

        assert event is not None
        data = json.loads(event.state_json)
        assert data["name"] == "root"
        assert data["parent"] == {"$drafter_ref": []}

    def test_parent_child_cycle_round_trips_with_identity(self):
        root = TreeNode(name="root")
        child = TreeNode(name="child", parent=root)
        root.children.append(child)

        event = serialize_state_snapshot(root, "index", {}, "save", "quick")
        assert event is not None
        restored = deserialize_state_snapshot(event.state_json, TreeNode(name=""))

        assert restored.name == "root"
        assert restored.children[0].name == "child"
        # The cycle is a real object cycle again, not a duplicate.
        assert restored.children[0].parent is restored

    def test_list_cycle_round_trips_without_a_state_class(self):
        data = [1, 2]
        data.append(data)

        event = serialize_state_snapshot(data, "index", {}, "save", "quick")
        assert event is not None
        restored = deserialize_state_snapshot(event.state_json, None)

        assert restored[0] == 1
        assert restored[2] is restored

    def test_dict_cycle_round_trips_without_a_state_class(self):
        data = {"name": "loop"}
        data["me"] = data

        event = serialize_state_snapshot(data, "index", {}, "save", "quick")
        assert event is not None
        restored = deserialize_state_snapshot(event.state_json, None)

        assert restored["name"] == "loop"
        assert restored["me"] is restored

    def test_shared_but_acyclic_objects_still_encode(self):
        shared = TreeNode(name="shared")
        root = TreeNode(name="root", children=[shared, shared])

        event = serialize_state_snapshot(root, "index", {}, "save", "quick")

        assert event is not None
        data = json.loads(event.state_json)
        # Shared (non-cyclic) references are duplicated, as before.
        assert data["children"][0]["name"] == "shared"
        assert data["children"][1]["name"] == "shared"


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


def make_bridge_stand_in(server, state_display: bool = True):
    """ClientBridge.save/load_state_snapshot only touch the navigator, the
    site title, the `state_display` setting, and the injected server hooks
    (built here the same way bridger builds them), so a minimal stand-in
    works."""
    navigator = MagicMock()
    navigator.last_request = None
    navigator.last_request_state_json = None
    hooks = build_server_hooks(server, MagicMock(), MagicMock(), MagicMock())
    return SimpleNamespace(
        navigator=navigator,
        site_title="Test Site",
        configuration=SimpleNamespace(state_display=state_display),
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
        # No request has run, so there is no earlier state to carry.
        assert published[0].state_before_json == ""

    def test_carries_the_state_from_before_the_last_request(
        self, captured_events, fresh_server
    ):
        fresh_server.state.update(GameState(score=7, name="Dot"))
        bridge = make_bridge_stand_in(fresh_server)
        bridge.navigator.last_request = Request("form", "guess", {"answer": 4}, {}, "")
        bridge.navigator.last_request_state_json = json.dumps(
            {"score": 6, "name": "Dot", "inventory": None}
        )
        event = SimpleNamespace(detail=SimpleNamespace(reason="save", slot="quick"))

        ClientBridge.save_state_snapshot(bridge, event)

        (snapshot,) = events_of_type(captured_events, "StateSnapshot")
        assert snapshot.version == SNAPSHOT_VERSION == 2
        assert json.loads(snapshot.state_json)["score"] == 7
        assert json.loads(snapshot.state_before_json)["score"] == 6
        payload = snapshot.to_json()
        assert payload["state_before_json"] == snapshot.state_before_json
        # The whole event must survive JSON encoding (it crosses the bridge).
        json.dumps(payload)


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

    def test_restored_state_stays_hidden_when_the_display_is_off(
        self, captured_events, fresh_server
    ):
        fresh_server.state.update(GameState(score=0, name="start"))
        bridge = make_bridge_stand_in(fresh_server, state_display=False)
        event = self.make_load_event(GameState(score=99, name="saved"), "guess")

        ClientBridge.load_state_snapshot(bridge, event)

        assert fresh_server.state.current == GameState(score=99, name="saved")
        (state_event,) = events_of_type(captured_events, "UpdatedState")
        assert state_event.representation["kind"] == "hidden"
        assert state_event.representation["type"] == "GameState"

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

    def test_restores_the_earlier_state_when_the_snapshot_has_one(
        self, captured_events, fresh_server
    ):
        fresh_server.state.update(GameState(score=0, name="start"))
        bridge = make_bridge_stand_in(fresh_server)
        event = self.make_load_event(GameState(score=5, name="after"), "guess")
        event.detail.state_before_json = serialize_state_snapshot(
            GameState(score=4, name="before"), "guess", {}, "save", "quick"
        ).state_json

        ClientBridge.load_state_snapshot(bridge, event)

        # The route then runs against the earlier state and redoes its step.
        assert fresh_server.state.current == GameState(score=4, name="before")
        bridge.navigator.goto.assert_called_once_with("guess", {}, action="system")

    def test_empty_earlier_state_falls_back_to_the_saved_state(
        self, captured_events, fresh_server
    ):
        fresh_server.state.update(GameState(score=0, name="start"))
        bridge = make_bridge_stand_in(fresh_server)
        event = self.make_load_event(GameState(score=5, name="after"), "guess")
        event.detail.state_before_json = ""

        ClientBridge.load_state_snapshot(bridge, event)

        assert fresh_server.state.current == GameState(score=5, name="after")

    def test_unusable_earlier_state_reports_error_and_changes_nothing(
        self, captured_events, fresh_server
    ):
        fresh_server.state.update(GameState(score=1, name="keep"))
        bridge = make_bridge_stand_in(fresh_server)
        event = self.make_load_event(GameState(score=5, name="after"), "guess")
        event.detail.state_before_json = json.dumps({"unrelated": True})

        ClientBridge.load_state_snapshot(bridge, event)

        assert fresh_server.state.current == GameState(score=1, name="keep")
        bridge.navigator.goto.assert_not_called()
        assert len(events_of_type(captured_events, "client.load_snapshot_failed")) == 1


@dataclass
class Counter:
    """State of the counting app used for the save-then-load round trip."""

    count: int


class TestSaveThenLoadRoundTrip:
    """Saving on a page whose route changed the state, then loading, must
    come back to that page and state, not to one step past it."""

    def make_counting_app(self, server):
        """Wire a real server and NavigationController to a bridge stand-in.

        Returns the stand-in and the list of Responses the navigator got.
        """

        def index(state: Counter) -> Page:
            return Page(state, [f"Count: {state.count}"])

        def add(state: Counter) -> Page:
            state.count += 1
            return Page(state, [f"Count: {state.count}"])

        server.do_configuration()
        server.do_start()
        server.add_route("index", index)
        server.add_route("add", add)
        server.state.update(Counter(0))
        hooks = build_server_hooks(server, MagicMock(), MagicMock(), MagicMock())
        responses = []

        def visit(request):
            response = server.do_visit(request)
            responses.append(response)
            return response

        runtime = MagicMock()
        # The page's address names no route, so the app opens on its index.
        runtime.create_url.return_value.searchParams.get.return_value = None
        navigator = NavigationController(runtime)
        navigator.set_navigation_func(visit)
        navigator.set_state_accessors(hooks.get_state, hooks.set_state)
        bridge = SimpleNamespace(
            navigator=navigator,
            site_title="Counter",
            configuration=SimpleNamespace(state_display=True),
            hooks=hooks,
            _require_hooks=lambda: hooks,
        )
        return bridge, responses

    def save(self, bridge, captured_events):
        ClientBridge.save_state_snapshot(
            bridge, SimpleNamespace(detail=SimpleNamespace(reason="save", slot="quick"))
        )
        return events_of_type(captured_events, "StateSnapshot")[-1]

    def test_snapshot_saved_after_add_loads_back_to_the_same_count(
        self, captured_events, fresh_server
    ):
        bridge, responses = self.make_counting_app(fresh_server)
        bridge.navigator.do_initial_request()
        bridge.navigator.goto("add", {}, action="link")
        assert fresh_server.state.current == Counter(1)
        snapshot = self.save(bridge, captured_events)
        # The student keeps clicking after the save.
        bridge.navigator.goto("add", {}, action="link")
        bridge.navigator.goto("add", {}, action="link")
        assert fresh_server.state.current == Counter(3)

        # What js/src/debug/saveload.tsx sends back for this snapshot.
        ClientBridge.load_state_snapshot(
            bridge,
            SimpleNamespace(
                detail=SimpleNamespace(
                    state_json=snapshot.state_json,
                    state_before_json=snapshot.state_before_json,
                    route=snapshot.route,
                    kwargs_json=snapshot.kwargs_json,
                )
            ),
        )

        assert snapshot.route == "add"
        assert json.loads(snapshot.state_json) == {"count": 1}
        assert json.loads(snapshot.state_before_json) == {"count": 0}
        assert fresh_server.state.current == Counter(1)
        assert "Count: 1" in responses[-1].body

    def test_snapshot_of_the_first_page_carries_the_starting_state(
        self, captured_events, fresh_server
    ):
        # The initial page load pushes no history entry, so its earlier
        # state has to be captured separately.
        bridge, _responses = self.make_counting_app(fresh_server)
        bridge.navigator.do_initial_request()

        snapshot = self.save(bridge, captured_events)

        assert snapshot.route == "index"
        assert json.loads(snapshot.state_before_json) == {"count": 0}

    def test_earlier_state_is_kept_when_browser_history_is_off(
        self, captured_events, fresh_server
    ):
        # Embedded instances push no history entries at all.
        bridge, _responses = self.make_counting_app(fresh_server)
        bridge.navigator.browser_history_enabled = False
        bridge.navigator.do_initial_request()
        bridge.navigator.goto("add", {}, action="link")

        snapshot = self.save(bridge, captured_events)

        assert json.loads(snapshot.state_json) == {"count": 1}
        assert json.loads(snapshot.state_before_json) == {"count": 0}
        bridge.navigator.history.runtime.history_push_state.assert_not_called()

    def test_snapshot_in_the_old_format_still_loads_the_old_way(
        self, captured_events, fresh_server
    ):
        # A snapshot stored before the earlier state was saved has only
        # the state from after its route ran. It keeps loading as it always
        # did: that state is restored and the route runs on top of it.
        bridge, responses = self.make_counting_app(fresh_server)
        bridge.navigator.do_initial_request()

        ClientBridge.load_state_snapshot(
            bridge,
            SimpleNamespace(
                detail=SimpleNamespace(
                    state_json=json.dumps({"count": 1}),
                    route="add",
                    kwargs_json="{}",
                )
            ),
        )

        assert fresh_server.state.current == Counter(2)
        assert "Count: 2" in responses[-1].body

    def test_unencodable_state_is_skipped_without_a_report(self, captured_events):
        # A state that cannot be reduced to simple data, on a request that
        # pushes no history entry: there is no earlier state to keep, and
        # nothing is reported (saving a snapshot reports it, once).
        navigator = NavigationController(MagicMock())
        navigator.set_navigation_func(lambda request: None)
        navigator.set_state_accessors(lambda: (lambda: None), lambda value: None)

        navigator.navigate(Request("link", "index", {}, {}, ""), remember=False)

        assert navigator.last_request_state_json is None
        assert [e.kind for e in captured_events if e.kind.startswith("bridge.")] == []
