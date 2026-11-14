"""Tests for how the ClientBridge receives configuration updates.

Every `reconfigure` call publishes an UpdatedConfiguration event that the
bridge sees (calls made before `start_server` are replayed to it). Settings
that change nothing in the page must be accepted quietly: reporting them
put a "Drafter had trouble syncing your Python code with the browser"
error in the debug panel of every site that called `set_site_information`.
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.client_bridge import ClientBridge
from drafter.client_server import commands
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import set_main_server
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.details.config import UpdatedConfigurationEvent
from drafter.deploy import set_browser_history, set_site_information

UNHANDLED = "client.unhandled_config_update"


@pytest.fixture(autouse=True)
def isolate_main_server():
    """Save and restore the global current-server pointer around each test."""
    saved = commands.MAIN_SERVER
    yield
    commands.MAIN_SERVER = saved


@pytest.fixture
def server():
    """A server made current, so bridge error reports publish on its bus."""
    server = ClientServer("test-config-updates")
    set_main_server(server)
    return server


def make_bridge(configuration: ClientServerConfiguration) -> ClientBridge:
    """A ClientBridge with a quiet debug panel and no DOM or runtime."""
    bridge = ClientBridge.__new__(ClientBridge)
    bridge.configuration = configuration
    bridge.debug_panel = SimpleNamespace(handleEvent=lambda event: True)
    bridge.runtime = SimpleNamespace(convert_to_js=lambda event: event)
    bridge.site_renderer = MagicMock()
    bridge.context = MagicMock()
    bridge.events = MagicMock()
    bridge.navigator = MagicMock()
    bridge._forwarding_debug_event = False
    bridge._applied_content = set()
    return bridge


def connect(server: ClientServer) -> list:
    """Subscribe a bridge to the server's events; return the events seen."""
    seen: list = []
    server.event_bus.subscribe("*", seen.append)
    bridge = make_bridge(server.get_default_configuration())
    server.event_bus.subscribe("*", bridge.handle_server_event)
    return seen


def kinds(events: list) -> list[str]:
    return [event.kind for event in events]


class TestSettingsWithoutPageEffect:
    def test_set_site_information_reports_no_error(self, server):
        seen = connect(server)

        set_site_information(
            author="Ada Lovelace",
            description="Counts corgi puppies.",
            sources="",
            planning="planning.pdf",
            links=["https://github.com/ada/corgi-count"],
            server=server,
        )

        assert kinds(seen).count("UpdatedConfiguration") == 5
        assert UNHANDLED not in kinds(seen)

    def test_set_browser_history_reports_no_error(self, server):
        seen = connect(server)

        set_browser_history(False, server=server)

        assert UNHANDLED not in kinds(seen)

    @pytest.mark.parametrize(
        "key",
        [
            *ClientServerConfiguration.SITE_INFORMATION_KEYS,
            "browser_history",
            "console_mode",
            "external_pages",
            "newlines_to_br",
        ],
    )
    def test_real_setting_is_accepted(self, server, key):
        seen = connect(server)
        bridge = make_bridge(ClientServerConfiguration())

        handled = bridge.handle_server_event(
            UpdatedConfigurationEvent(key=key, value="anything")
        )

        # Still forwarded to the debug panel, which lists configuration.
        assert handled is True
        assert UNHANDLED not in kinds(seen)


class TestUnknownSetting:
    def test_unknown_key_is_still_reported(self, server):
        seen = connect(server)
        bridge = make_bridge(ClientServerConfiguration())

        bridge.handle_server_event(
            UpdatedConfigurationEvent(key="not_a_real_setting", value=1)
        )

        assert kinds(seen).count(UNHANDLED) == 1
