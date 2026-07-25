"""Tests for runtime theme switching (debug menu View > Switch Theme).

The JS dialog dispatches a ``drafter-set-theme`` window event; the bridge
answers with a server reconfigure, whose UpdatedConfiguration telemetry
loops back into handle_server_event, which swaps only the connected theme
stylesheet links (no page reload) via SiteRenderer.refresh_theme_css.
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.client_bridge import ClientBridge
from drafter.bridge.site_renderer import SiteRenderer
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import (
    get_main_event_bus,
    get_main_server,
    set_main_server,
)
from drafter.site.site import DRAFTER_TAG_CLASSES


@pytest.fixture
def fresh_server():
    """Install a throwaway main server so tests never mutate a shared one."""
    previous = get_main_server()
    server = ClientServer("THEME_TEST_SERVER")
    set_main_server(server)
    yield server
    set_main_server(previous)


@pytest.fixture
def captured_events(fresh_server):
    """Capture all telemetry published during a test (on the fresh server's bus)."""
    events = []
    bus = get_main_event_bus()
    subscription = bus.subscribe("*", events.append)
    yield events
    bus.unsubscribe(subscription)


def events_of_type(events, kind):
    return [event for event in events if event.kind == kind]


def theme_event(detail):
    return SimpleNamespace(detail=detail)


class TestSetSiteTheme:
    def test_valid_theme_reconfigures_the_server(
        self, captured_events, fresh_server
    ):
        ClientBridge.set_site_theme(SimpleNamespace(), theme_event("sakura"))

        updates = events_of_type(captured_events, "UpdatedConfiguration")
        assert len(updates) == 1
        assert updates[0].key == "theme"
        assert updates[0].value == "sakura"

    def test_none_theme_is_accepted(self, captured_events, fresh_server):
        ClientBridge.set_site_theme(SimpleNamespace(), theme_event("none"))

        updates = events_of_type(captured_events, "UpdatedConfiguration")
        assert len(updates) == 1
        assert updates[0].value == "none"

    def test_unknown_theme_reports_a_suggestion(
        self, captured_events, fresh_server
    ):
        ClientBridge.set_site_theme(SimpleNamespace(), theme_event("skelton"))

        assert not events_of_type(captured_events, "UpdatedConfiguration")
        errors = events_of_type(captured_events, "client.set_theme_unknown")
        assert len(errors) == 1
        assert "skeleton" in errors[0].error.message

    def test_missing_name_reports_error(self, captured_events, fresh_server):
        ClientBridge.set_site_theme(SimpleNamespace(), theme_event(None))

        assert not events_of_type(captured_events, "UpdatedConfiguration")
        assert (
            len(events_of_type(captured_events, "client.set_theme_missing_name"))
            == 1
        )


class TestHandleServerEventTheme:
    def test_theme_update_refreshes_the_site_css(self, fresh_server):
        from drafter.data.details.config import UpdatedConfigurationEvent

        bridge = SimpleNamespace(
            configuration=SimpleNamespace(theme="default"),
            site_renderer=MagicMock(),
            _refresh_site_theme=MagicMock(),
            _handle_debug_events=MagicMock(return_value=True),
        )
        event = UpdatedConfigurationEvent(key="theme", value="sakura")

        handled = ClientBridge.handle_server_event(bridge, event)

        assert handled is True
        assert bridge.configuration.theme == "sakura"
        bridge._refresh_site_theme.assert_called_once_with()


class FakeLink:
    """Minimal stand-in for a connected <link> element."""

    def __init__(self, href):
        self.href = href
        self.attributes = {"href": href}
        self.removed = False

    def getAttribute(self, name):
        return self.attributes.get(name)

    def setAttribute(self, name, value):
        self.attributes[name] = value

    def remove(self):
        self.removed = True


class TestRefreshThemeCss:
    def make_renderer(self, existing_links):
        renderer = SiteRenderer(MagicMock(), "root", "root")
        renderer.scope = MagicMock()
        renderer.use_shadow_dom = False
        renderer.document = MagicMock()
        renderer.document.querySelectorAll.return_value = existing_links
        return renderer

    def test_swaps_only_the_stale_link_tail(self, monkeypatch):
        # Cascade: [global debug css, theme css, built-ins]. Switching the
        # theme keeps the global link connected and replaces the rest.
        existing = [
            FakeLink("assets/css/drafter_debug.css"),
            FakeLink("assets/css/default.css"),
            FakeLink("assets/css/drafter_base.css"),
        ]
        renderer = self.make_renderer(existing)
        added = []
        monkeypatch.setattr(
            "drafter.bridge.site_renderer.add_link",
            lambda root, url, with_class="": added.append((url, with_class)),
        )

        renderer.refresh_theme_css(
            [
                "assets/css/drafter_debug.css",
                "assets/css/sakura.css",
                "assets/css/drafter_base.css",
            ]
        )

        # The matching prefix stays connected (no CSS refetch/flash)...
        assert existing[0].removed is False
        # ...the stale tail is removed...
        assert existing[1].removed is True
        assert existing[2].removed is True
        # ...and the remaining wanted links are created in cascade order,
        # tagged with the theme class.
        theme_class = DRAFTER_TAG_CLASSES["THEME"]
        assert added == [
            ("assets/css/sakura.css", theme_class),
            ("assets/css/drafter_base.css", theme_class),
        ]

    def test_no_scope_is_a_safe_no_op(self):
        renderer = SiteRenderer(MagicMock(), "root", "root")
        renderer.scope = None

        renderer.refresh_theme_css(["assets/css/sakura.css"])
