"""Tests for the DRAFTER_SKIP setting.

The skip setting makes start_server() do nothing at all — no server startup,
no site compilation — so that a site file can be imported (e.g., by a unit
test runner) without launching anything. It lives on BootstrapConfiguration
and can be set via the DRAFTER_SKIP environment variable, the --skip command
line flag, a config file, or start_server(skip=True).
"""

import argparse
from unittest.mock import MagicMock

import pytest

import drafter.launch
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.configuration import (
    _reset_system_for_testing,
    _set_system_for_testing,
    configure_system,
)
from drafter.launch import start_server


def make_system(**bootstrap_kwargs) -> SystemConfiguration:
    return SystemConfiguration(
        bootstrap=BootstrapConfiguration(path="main.py", **bootstrap_kwargs),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(),
        app_common=AppCommonConfiguration(),
    )


@pytest.fixture
def injected_system():
    """Inject a fresh SystemConfiguration and reset it afterwards."""

    def inject(**bootstrap_kwargs) -> SystemConfiguration:
        system = make_system(**bootstrap_kwargs)
        _set_system_for_testing(system)
        return system

    yield inject
    _reset_system_for_testing()


class TestSkipDefaults:
    def test_default_is_false(self):
        assert BootstrapConfiguration().skip is False

    def test_to_json_includes_skip(self):
        assert BootstrapConfiguration(skip=True).to_json()["skip"] is True

    def test_copy_preserves_skip(self):
        assert BootstrapConfiguration(skip=True).copy().skip is True


class TestSkipEnvVar:
    @pytest.mark.parametrize("value", ["1", "true", "True", "yes"])
    def test_truthy_values(self, value):
        parsed = BootstrapConfiguration.parse_env_variables({"DRAFTER_SKIP": value})
        assert parsed["skip"] is True

    @pytest.mark.parametrize("value", ["0", "false", "no", ""])
    def test_falsy_values(self, value):
        parsed = BootstrapConfiguration.parse_env_variables({"DRAFTER_SKIP": value})
        assert parsed["skip"] is False

    def test_absent(self):
        assert "skip" not in BootstrapConfiguration.parse_env_variables({})

    def test_configure_system_reads_env_var(self, monkeypatch):
        monkeypatch.setenv("DRAFTER_SKIP", "1")
        monkeypatch.setattr("sys.argv", ["my_site.py"])
        system, modified = configure_system()
        assert system.bootstrap.skip is True
        assert modified["bootstrap"]["skip"] is True


class TestSkipCli:
    def make_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        BootstrapConfiguration.extend_parser(parser)
        return parser

    def test_skip_flag(self):
        parsed, _ = self.make_parser().parse_known_args(["--skip"])
        assert BootstrapConfiguration.parse_args(vars(parsed))["skip"] is True

    def test_flag_not_given(self):
        parsed, _ = self.make_parser().parse_known_args([])
        assert "skip" not in BootstrapConfiguration.parse_args(vars(parsed))


class TestSkipConfigSetting:
    def test_merges_into_configuration(self):
        # Config file sections are applied through merge_in_args.
        config = BootstrapConfiguration()
        config.merge_in_args({"skip": True}, raise_errors=False)
        assert config.skip is True


class TestStartServerSkips:
    def test_skip_from_configuration(self, injected_system, monkeypatch):
        injected_system(skip=True)
        get_main_server = MagicMock()
        monkeypatch.setattr(drafter.launch, "get_main_server", get_main_server)
        start_server()
        get_main_server.assert_not_called()

    def test_skip_keyword_argument(self, injected_system, monkeypatch):
        system = injected_system()
        get_main_server = MagicMock()
        monkeypatch.setattr(drafter.launch, "get_main_server", get_main_server)
        start_server(skip=True)
        assert system.bootstrap.skip is True
        get_main_server.assert_not_called()

    def test_no_skip_starts_server(self, injected_system, monkeypatch):
        injected_system()
        serve_app_once = MagicMock()
        monkeypatch.setattr(drafter.launch, "get_main_server", MagicMock())
        monkeypatch.setattr("drafter.app.app_server.serve_app_once", serve_app_once)
        start_server()
        serve_app_once.assert_called_once()
