"""Tests for instance teardown and the debug-event recursion guard.

Covers the two halves of the "Toggle Frame freezes the tab after an
editor-driven restart" bug: the error-reporting recursion in
ClientBridge._handle_debug_events, and the stale listeners left behind
because reset_server_for_root never disconnected the old bridge.
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.client_bridge import ClientBridge
from drafter.bridge.events import EventManager
from drafter.client_server import commands
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import (
    register_instance_cleanup,
    register_server,
    reset_server_for_root,
    set_main_server,
)
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.details.config import UpdatedConfigurationEvent
from drafter.monitor.audit import log_record


@pytest.fixture(autouse=True)
def isolate_main_server():
    """Save and restore the global current-server pointer around each test."""
    saved = commands.MAIN_SERVER
    yield
    commands.MAIN_SERVER = saved


class FailingDebugPanel:
    """Debug panel stub whose handleEvent always throws (destroyed DOM)."""

    def __init__(self):
        self.calls = 0

    def handleEvent(self, event):
        self.calls += 1
        raise RuntimeError("DebugPanel: Config section not found.")


def make_bridge_with_failing_panel() -> tuple[ClientBridge, FailingDebugPanel]:
    """A ClientBridge wired to a panel that throws, without DOM/runtime."""
    panel = FailingDebugPanel()
    bridge = ClientBridge.__new__(ClientBridge)
    bridge.configuration = ClientServerConfiguration()
    bridge.debug_panel = panel
    bridge.runtime = SimpleNamespace(convert_to_js=lambda event: event)
    bridge.site_renderer = MagicMock()
    bridge.context = MagicMock()
    bridge.events = MagicMock()
    bridge._forwarding_debug_event = False
    return bridge, panel


class TestDebugEventRecursionGuard:
    def test_failing_panel_does_not_recurse(self):
        """A panel failure publishes an error on the same bus the bridge is
        subscribed to; without the guard this recurses without bound."""
        server = ClientServer("test-recursion")
        bridge, panel = make_bridge_with_failing_panel()
        server.event_bus.subscribe("*", bridge.handle_server_event)
        set_main_server(server)

        with pytest.raises(RuntimeError):
            log_record(
                UpdatedConfigurationEvent(
                    key="framed", value=False, update_default=False
                ),
                "tests.recursion",
            )

        # The original event reached the panel once; the error event it
        # produced was dropped by the guard instead of re-entering the panel.
        assert panel.calls == 1
        # The guard reset itself, so later events are forwarded again.
        assert bridge._forwarding_debug_event is False
        with pytest.raises(RuntimeError):
            log_record(
                UpdatedConfigurationEvent(
                    key="framed", value=True, update_default=False
                ),
                "tests.recursion",
            )
        assert panel.calls == 2


class FakeRuntime:
    """RuntimeAdapter stand-in that records wrapped/cleaned handlers."""

    def __init__(self):
        self.context = SimpleNamespace(window=MagicMock(), document=MagicMock())
        self.cleaned = []

    def wrap_event_handler(self, handler):
        return handler

    def cleanup_event_handler(self, handler):
        self.cleaned.append(handler)


class TestEventManagerTeardown:
    def test_teardown_removes_window_and_hotkey_listeners(self):
        runtime = FakeRuntime()
        manager = EventManager(runtime)
        handlers = {
            "drafter-toggle-frame": lambda event: None,
            "drafter-navigate": lambda event: None,
        }
        manager.setup_events(handlers, {"Q": lambda: None})
        assert runtime.context.window.addEventListener.call_count == 2
        assert runtime.context.document.addEventListener.call_count == 1

        manager.teardown()

        removed = {
            call.args[0]
            for call in runtime.context.window.removeEventListener.call_args_list
        }
        assert removed == set(handlers)
        runtime.context.document.removeEventListener.assert_called_once()
        assert manager.listeners == {}
        assert manager.hotkey_listener is None
        assert manager.hotkey_events == {}
        # Window and hotkey handler proxies were all released.
        assert len(runtime.cleaned) == 3

    def test_teardown_survives_dead_window(self):
        runtime = FakeRuntime()
        manager = EventManager(runtime)
        manager.setup_events({"drafter-toggle-frame": lambda event: None}, {})
        runtime.context.window.removeEventListener.side_effect = RuntimeError(
            "window detached"
        )
        manager.teardown()
        assert manager.listeners == {}


class TestResetServerTeardown:
    def test_reset_runs_registered_cleanup(self):
        """The cleanup registered by the composition root (mirroring
        run_client_bridge's teardown_instance closure) disconnects the bridge
        and the bus subscription when the instance is reset."""
        server = ClientServer("test-reset")
        bridge = MagicMock()
        subscription = server.do_listen_for_events(lambda event: None)
        register_server("embed-test", server)
        register_instance_cleanup(
            "embed-test",
            lambda: (
                bridge.teardown(),
                server.event_bus.unsubscribe(subscription),
            ),
        )
        assert commands.MAIN_SERVER is server

        reset_server_for_root("embed-test")

        bridge.teardown.assert_called_once()
        assert all(
            subscription.topic != "*" for subscription in server.event_bus.subscribers
        )
        assert commands.MAIN_SERVER is None
        # Idempotent for unknown/already-reset keys; the cleanup ran once.
        reset_server_for_root("embed-test")
        bridge.teardown.assert_called_once()

    def test_reset_survives_failing_cleanup(self):
        server = ClientServer("test-reset-failing")
        register_server("embed-test-2", server)

        def failing_cleanup():
            raise RuntimeError("boom")

        register_instance_cleanup("embed-test-2", failing_cleanup)

        reset_server_for_root("embed-test-2")

        assert commands.MAIN_SERVER is None
        assert "embed-test-2" not in commands._INSTANCE_CLEANUPS


class TestTornDownNavigation:
    """A click collects its form data through a promise chain, so its
    navigation can land after the instance was reset. It must be dropped:
    dispatching it would re-pin the dead server as current (the next run's
    routes and start_server would attach to it) and re-render the dead
    instance's page into the live root."""

    def _navigator(self):
        from drafter.bridge.navigation import NavigationController

        navigator = NavigationController(MagicMock())
        visit = MagicMock(name="visit")
        navigator.set_navigation_func(visit)
        navigator.history = MagicMock()
        return navigator, visit

    def test_navigate_after_teardown_is_dropped(self):
        from drafter.data.request import Request

        navigator, visit = self._navigator()
        navigator.teardown()

        result = navigator.navigate(Request("link", "update", {}, {}, ""))

        assert result is None
        visit.assert_not_called()
        navigator.history.add_to_history.assert_not_called()

    def test_popstate_after_teardown_is_dropped(self):
        navigator, visit = self._navigator()
        navigator.teardown()

        navigator.handle_popstate(SimpleNamespace(state=SimpleNamespace(request_id=1)))

        visit.assert_not_called()
        navigator.history.convert_popstate_to_request.assert_not_called()

    def test_navigate_before_teardown_still_dispatches(self):
        from drafter.data.request import Request

        navigator, visit = self._navigator()
        navigator.navigate(Request("link", "update", {}, {}, ""))
        visit.assert_called_once()

    def test_bridge_teardown_disables_navigator(self):
        bridge = ClientBridge.__new__(ClientBridge)
        bridge.navigator = MagicMock()
        bridge.events = MagicMock()
        bridge.debug_panel = MagicMock()

        bridge.teardown()

        bridge.navigator.teardown.assert_called_once()
        bridge.events.teardown.assert_called_once()
        assert bridge.debug_panel is None
