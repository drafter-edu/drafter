"""Tests for the `state_display` configuration setting (drafter-edu/drafter#171).

When enabled (the default), every state change is described in full for the
debug panel's Current State section. When disabled, the state is not walked
at all: the update event carries a tiny `hidden` representation naming only
the state's type, which the panel shows as a one-line note.
"""

import argparse
import sys
from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.navigation import NavigationController
from drafter.client_server import client_server as client_server_module
from drafter.client_server.client_server import ClientServer
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.details.state import UpdatedStateEvent, hidden_representation
from drafter.data.request import Request
from drafter.deploy import set_state_display
from drafter.payloads.kinds.page import Page


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    ClientServerConfiguration.extend_parser(parser)
    return parser


@dataclass
class Scoreboard:
    scores: list[int] = field(default_factory=lambda: [3, 1, 4])


class TestConfigurationPipeline:
    def test_default_is_enabled(self):
        assert ClientServerConfiguration().state_display is True

    def test_to_json_includes_state_display(self):
        as_json = ClientServerConfiguration(state_display=False).to_json()
        assert as_json["state_display"] is False

    def test_copy_preserves_state_display(self):
        copied = ClientServerConfiguration(state_display=False).copy()
        assert copied.state_display is False

    def test_environment_variable(self):
        result = ClientServerConfiguration.parse_env_variables(
            {"DRAFTER_STATE_DISPLAY": "false"}
        )
        assert result["state_display"] is False

    def test_environment_variable_absent(self):
        result = ClientServerConfiguration.parse_env_variables({})
        assert "state_display" not in result

    def test_cli_flag_disables(self):
        parsed, _ = make_parser().parse_known_args(["--no-state-display"])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert result["state_display"] is False

    def test_cli_flag_absent_leaves_other_sources_alone(self):
        parsed, _ = make_parser().parse_known_args([])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert "state_display" not in result


class TestSetStateDisplayHelper:
    def make_server(self):
        server = MagicMock()
        server.settings = {}
        server.reconfigure = lambda **kwargs: server.settings.update(kwargs)
        return server

    def test_disable(self):
        server = self.make_server()
        set_state_display(False, server=server)
        assert server.settings == {"state_display": False}

    def test_default_enables(self):
        server = self.make_server()
        set_state_display(server=server)
        assert server.settings == {"state_display": True}


class TestUpdatedStateEvent:
    def test_displayed_state_is_described_in_full(self):
        event = UpdatedStateEvent.from_state(Scoreboard())

        assert event.representation is not None
        assert event.representation["kind"] == "dataclass"

    def test_hidden_state_names_only_its_type(self):
        state = Scoreboard()

        event = UpdatedStateEvent.from_state(state, display=False)

        assert event.representation == {
            "kind": "hidden",
            "type": "Scoreboard",
            "id": id(state),
            "complexity": 0,
        }

    def test_hidden_state_is_never_walked(self):
        class Booby:
            """A state that fails the test if anything inspects it."""

            def __getattribute__(self, name):
                if name == "__class__":
                    return Booby
                raise AssertionError(f"state was inspected: {name}")

        assert hidden_representation(Booby())["type"] == "Booby"

    def test_hidden_representation_is_json_ready(self):
        event = UpdatedStateEvent.from_state([1, 2, 3], display=False)

        assert event.to_json()["representation"]["kind"] == "hidden"


class TestClientServer:
    """The server reads the setting each time it reports a state change."""

    @pytest.fixture
    def visit_state_kinds(self, monkeypatch):
        """Run one state-changing visit and report the state events' kinds."""

        def run(**settings) -> list[str]:
            server = ClientServer("state_display_test")
            server.do_configuration()
            server.do_start(Scoreboard())
            server.reconfigure(**settings)
            server.add_route("index", lambda: Page(Scoreboard([9, 9]), ["Hi"]))

            records = []
            original = client_server_module.log_record

            def recording_log_record(record, *args, **kwargs):
                records.append(record)
                return original(record, *args, **kwargs)

            monkeypatch.setattr(
                client_server_module, "log_record", recording_log_record
            )
            server.do_visit(Request("link", "index", {}, {}, ""))
            return [
                record.representation["kind"]
                for record in records
                if isinstance(record, UpdatedStateEvent)
            ]

        return run

    def test_state_is_described_by_default(self, visit_state_kinds):
        assert visit_state_kinds() == ["dataclass"]

    def test_state_is_hidden_when_turned_off(self, visit_state_kinds):
        assert visit_state_kinds(state_display=False) == ["hidden"]


class TestNavigationController:
    def test_defaults_to_displaying_state(self):
        assert NavigationController(MagicMock()).state_display is True


class TestBridge:
    """Changing the setting while the app runs reaches the bridge's copies."""

    def test_configuration_update_is_applied(self):
        from types import SimpleNamespace

        from drafter.bridge.client_bridge import ClientBridge
        from drafter.data.details.config import UpdatedConfigurationEvent

        bridge = SimpleNamespace(
            configuration=SimpleNamespace(state_display=True),
            navigator=SimpleNamespace(state_display=True),
            _handle_debug_events=MagicMock(return_value=True),
        )
        event = UpdatedConfigurationEvent(key="state_display", value=False)

        handled = ClientBridge.handle_server_event(bridge, event)

        assert handled is True
        assert bridge.configuration.state_display is False
        assert bridge.navigator.state_display is False
