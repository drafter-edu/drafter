"""Tests for SiteState copy semantics (history/state.py).

State snapshots stored in history should be deep copies by default so that
later in-place mutations do not rewrite earlier snapshots. When deep copy
fails (states can hold arbitrary objects), SiteState falls back to a shallow
copy, and finally to the original reference, logging a one-time warning via
the audit system.
"""

from dataclasses import dataclass, field

import pytest

from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import (
    get_main_event_bus,
    get_main_server,
    set_main_server,
)
from drafter.history.state import SiteState


@dataclass
class Inventory:
    items: list[str] = field(default_factory=list)


@dataclass
class PlayerState:
    score: int = 0
    inventory: Inventory = field(default_factory=Inventory)


class Undeepcopyable:
    """Deep copy raises, shallow copy works."""

    def __init__(self):
        self.tag = "original"

    def __deepcopy__(self, memo):
        raise TypeError("cannot deep copy this")


class Uncopyable:
    """Both deep and shallow copies raise."""

    def __deepcopy__(self, memo):
        raise TypeError("cannot deep copy this")

    def __copy__(self):
        raise TypeError("cannot shallow copy this")


@pytest.fixture
def fresh_server():
    """Install a throwaway main server so tests never mutate a shared one."""
    previous = get_main_server()
    server = ClientServer("SITE_STATE_TEST_SERVER")
    set_main_server(server)
    yield server
    set_main_server(previous)


@pytest.fixture
def captured_events(fresh_server):
    events = []
    bus = get_main_event_bus()
    subscription = bus.subscribe("*", events.append)
    yield events
    bus.unsubscribe(subscription)


class TestDeepCopySnapshots:
    def test_history_entries_are_independent_copies(self):
        site_state = SiteState()
        state = PlayerState(score=1, inventory=Inventory(items=["sword"]))
        site_state.update(state)

        state.score = 2
        state.inventory.items.append("shield")
        site_state.update(state)

        first, second = site_state.history
        assert first is not state
        assert first.score == 1
        assert first.inventory.items == ["sword"]
        assert second.score == 2
        assert second.inventory.items == ["sword", "shield"]

    def test_current_keeps_live_reference(self):
        site_state = SiteState()
        state = PlayerState()
        site_state.update(state)
        assert site_state.current is state

    def test_reset_restores_initial_deep_copy(self):
        site_state = SiteState()
        state = PlayerState(score=1, inventory=Inventory(items=["sword"]))
        site_state.update(state)
        state.score = 99
        state.inventory.items.clear()

        site_state.reset()

        assert site_state.current is not state
        assert site_state.current.score == 1
        assert site_state.current.inventory.items == ["sword"]
        assert site_state.history == []


class TestCopyFallbacks:
    def test_falls_back_to_shallow_copy(self, captured_events):
        site_state = SiteState()
        state = Undeepcopyable()
        site_state.update(state)

        snapshot = site_state.history[0]
        assert snapshot is not state
        assert snapshot.tag == "original"
        warnings = [
            event
            for event in captured_events
            if getattr(getattr(event, "error", None), "id", None)
            == "state.copy_fallback"
        ]
        assert warnings

    def test_falls_back_to_reference_when_all_copies_fail(self, captured_events):
        site_state = SiteState()
        state = Uncopyable()
        site_state.update(state)

        assert site_state.history[0] is state

    def test_fallback_warning_only_logged_once(self, captured_events):
        site_state = SiteState()
        site_state.update(Undeepcopyable())
        site_state.update(Undeepcopyable())
        site_state.update(Undeepcopyable())

        warnings = [
            event
            for event in captured_events
            if getattr(getattr(event, "error", None), "id", None)
            == "state.copy_fallback"
        ]
        assert len(warnings) == 1

    def test_shallow_fallback_shares_nested_data(self):
        site_state = SiteState()
        state = Undeepcopyable()
        state.nested = ["a"]
        site_state.update(state)

        state.nested.append("b")
        assert site_state.history[0].nested == ["a", "b"]
