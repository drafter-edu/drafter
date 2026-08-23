"""Tests for the `browser_history` configuration flag.

When enabled (the default for standalone sites), Drafter mirrors navigation
into the browser's history stack so back/forward time travel through the
app. When disabled, the bridge never touches the browser's history or URL:
no entries are pushed, the original entry is not stamped with the startup
state, and popstate events are ignored (they belong to the host page).
configure_instance() disables the flag automatically, since embedded
instances (like documentation demos) share their host page's history.
"""

import argparse
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from drafter.config.client_server import ClientServerConfiguration

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.navigation import NavigationController
from drafter.client_server import commands
from drafter.client_server.commands import (
    configure_instance,
    get_main_server,
    set_current_instance_root,
    set_main_server,
)
from drafter.configuration import get_system_configuration
from drafter.data.request import Request
from drafter.deploy import set_browser_history


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    ClientServerConfiguration.extend_parser(parser)
    return parser


class TestConfigurationPipeline:
    def test_default_is_enabled(self):
        assert ClientServerConfiguration().browser_history is True

    def test_to_json_includes_browser_history(self):
        as_json = ClientServerConfiguration(browser_history=False).to_json()
        assert as_json["browser_history"] is False

    def test_copy_preserves_browser_history(self):
        copied = ClientServerConfiguration(browser_history=False).copy()
        assert copied.browser_history is False

    def test_env_variable_disables(self):
        result = ClientServerConfiguration.parse_env_variables(
            {"DRAFTER_BROWSER_HISTORY": "false"}
        )
        assert result["browser_history"] is False

    def test_env_variable_absent_leaves_default(self):
        result = ClientServerConfiguration.parse_env_variables({})
        assert "browser_history" not in result

    def test_cli_flag_disables(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args(["--no-browser-history"])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert result["browser_history"] is False

    def test_cli_flag_not_given(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args([])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert "browser_history" not in result


class TestConfigureInstanceDisables:
    """Embedded (multi-instance) apps share the host page's history stack,
    so configure_instance turns browser history off by default."""

    @pytest.fixture
    def restored_globals(self):
        """Snapshot and restore everything configure_instance mutates."""
        system = get_system_configuration()
        saved_config = system.client_server.copy()
        previous_server = get_main_server()
        yield
        system.client_server = saved_config
        set_main_server(previous_server)
        set_current_instance_root(None)
        commands._PENDING_INSTANCE_CONTEXT = None

    def test_configure_instance_disables_browser_history(self, restored_globals):
        system = get_system_configuration()
        system.client_server.browser_history = True

        configure_instance("drafter-root-test-embed")

        assert system.client_server.browser_history is False
        assert system.client_server.root_element_id == "drafter-root-test-embed"


class TestNavigationGating:
    def make_navigator(self, enabled):
        navigator = NavigationController(MagicMock())
        navigator.history = MagicMock()
        navigator.browser_history_enabled = enabled
        dispatched = []
        navigator.set_navigation_func(
            lambda request: dispatched.append(request)
            or SimpleNamespace(url=request.url)
        )
        return navigator, dispatched

    def test_disabled_navigate_pushes_no_entries(self):
        navigator, dispatched = self.make_navigator(enabled=False)

        navigator.navigate(Request("link", "shop", {}, {}, ""), remember=True)

        # The visit itself still happens (and is still replayable)...
        assert dispatched[-1].url == "shop"
        assert navigator.last_request is dispatched[-1]
        # ...but the browser's history stack is never touched.
        navigator.history.add_to_history.assert_not_called()

    def test_disabled_initial_request_leaves_original_entry_alone(self):
        navigator, dispatched = self.make_navigator(enabled=False)

        navigator.do_initial_request()

        assert dispatched[-1].url == "index"
        navigator.history.record_initial_state.assert_not_called()

    def test_disabled_popstate_is_ignored(self):
        """A popstate on the shared window belongs to the host page: the
        bridge must not dispatch a request or rewrite the URL for it."""
        navigator, dispatched = self.make_navigator(enabled=False)
        event = SimpleNamespace(
            state=SimpleNamespace(request_id=5, url="shop", kwargs="{}")
        )

        navigator.handle_popstate(event)

        assert dispatched == []
        navigator.history.convert_popstate_to_request.assert_not_called()

    def test_enabled_behavior_is_unchanged(self):
        navigator, dispatched = self.make_navigator(enabled=True)

        navigator.navigate(Request("link", "shop", {}, {}, ""), remember=True)
        navigator.do_initial_request()

        navigator.history.add_to_history.assert_called_once()
        navigator.history.record_initial_state.assert_called_once()


class TestSetBrowserHistoryHelper:
    def make_server(self):
        server = MagicMock()
        server.settings = {}
        server.reconfigure = lambda **kwargs: server.settings.update(kwargs)
        return server

    def test_disable(self):
        server = self.make_server()
        set_browser_history(False, server=server)
        assert server.settings == {"browser_history": False}

    def test_default_enables(self):
        server = self.make_server()
        set_browser_history(server=server)
        assert server.settings == {"browser_history": True}
