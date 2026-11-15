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


class TestSettingsMadeBeforeTheSiteStarted:
    """Updates from before the bridge existed are already in the first render.

    Applying them again undid `set_website_framed(False)` (the update is a
    toggle) and let an older `set_website_title` replace the title given to
    `start_server`.
    """

    def test_replayed_frame_update_does_not_toggle_the_frame(self, server):
        bridge = make_bridge(ClientServerConfiguration())
        bridge.replaying_startup_events = True

        handled = bridge.handle_server_event(
            UpdatedConfigurationEvent(key="framed", value=False)
        )

        bridge.site_renderer.toggle_frame.assert_not_called()
        # The debug panel still lists the change.
        assert handled is True

    def test_live_frame_update_still_toggles_the_frame(self, server):
        bridge = make_bridge(ClientServerConfiguration())

        bridge.handle_server_event(UpdatedConfigurationEvent(key="framed", value=False))

        bridge.site_renderer.toggle_frame.assert_called_once()

    def test_replayed_title_does_not_replace_the_rendered_one(self, server):
        configuration = ClientServerConfiguration(site_title="From start_server")
        bridge = make_bridge(configuration)
        bridge.replaying_startup_events = True

        bridge.handle_server_event(
            UpdatedConfigurationEvent(key="site_title", value="From the function")
        )

        assert configuration.site_title == "From start_server"

    def test_startup_replays_with_the_flag_set_and_clears_it(self, server, monkeypatch):
        from drafter.bridge import bridger

        flags_seen: list[tuple[str, bool]] = []

        class RecordingBridge:
            replaying_startup_events = False

            def __init__(self, configuration, context=None):
                pass

            def setup_site(self, rendered_site):
                pass

            def handle_server_event(self, event):
                flags_seen.append((event.kind, self.replaying_startup_events))

            def setup_events(self, hooks):
                pass

            def start(self):
                # Made after start-up, so it has to reach the page.
                server.reconfigure(framed=True)
                self.flag_at_start = self.replaying_startup_events

        created: list[RecordingBridge] = []

        def make_recording_bridge(configuration, context=None):
            created.append(RecordingBridge(configuration, context))
            return created[-1]

        monkeypatch.setattr(bridger, "ClientBridge", make_recording_bridge)
        monkeypatch.setattr(bridger.DomContext, "for_window", lambda window: None)
        # Made before start-up, the way set_website_framed(False) is.
        server.reconfigure(framed=False)

        bridger.run_client_bridge(MagicMock(), server, None)

        updates = [flag for kind, flag in flags_seen if kind == "UpdatedConfiguration"]
        assert updates == [True, False]
        assert created[0].flag_at_start is False
