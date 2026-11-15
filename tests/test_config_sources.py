"""Tests for how settings from different sources are layered.

Command line flags outrank environment variables, which outrank the
built-in defaults. A flag that was not given must leave the lower layers
alone, and a config file must load without disturbing the rest.
"""

import argparse
import builtins
import json

import pytest

from drafter.config.app_server import DEFAULT_PORT, AppServerConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.configuration import configure_system
from drafter.files.opening import open as drafter_open


def parse_app_server(argv: list[str]) -> dict:
    parser = argparse.ArgumentParser()
    AppServerConfiguration.extend_parser(parser)
    parsed, _ = parser.parse_known_args(argv)
    return AppServerConfiguration.parse_args(vars(parsed))


APP_SERVER_ENVIRONMENT = {
    "DRAFTER_PORT": "8123",
    "DRAFTER_HOST": "0.0.0.0",
    "DRAFTER_USE_RELOADER": "false",
    "DRAFTER_OPEN_BROWSER": "false",
    "DRAFTER_INLINE_PY": "false",
    "DRAFTER_SERVE_ADJACENT_FILES": "false",
}

APP_SERVER_FROM_ENVIRONMENT = {
    "port": 8123,
    "host": "0.0.0.0",
    "use_reloader": False,
    "open_browser": False,
    "inline_py": False,
    "serve_adjacent_files": False,
}


class TestAppServerEnvironmentVariables:
    """These six used to be overwritten by argparse defaults every time."""

    def test_flags_left_off_report_nothing(self):
        assert parse_app_server([]) == {}

    def test_environment_variables_are_used_without_flags(self, monkeypatch):
        for name, value in APP_SERVER_ENVIRONMENT.items():
            monkeypatch.setenv(name, value)
        monkeypatch.setattr("sys.argv", ["my_site.py"])

        system, modified = configure_system()

        for field_name, expected in APP_SERVER_FROM_ENVIRONMENT.items():
            assert getattr(system.app_server, field_name) == expected
        assert modified["app_server"] == APP_SERVER_FROM_ENVIRONMENT

    def test_flags_still_outrank_environment_variables(self, monkeypatch):
        monkeypatch.setenv("DRAFTER_PORT", "8123")
        monkeypatch.setenv("DRAFTER_HOST", "0.0.0.0")
        monkeypatch.setenv("DRAFTER_OPEN_BROWSER", "true")
        monkeypatch.setattr(
            "sys.argv",
            [
                "my_site.py",
                "--port",
                "9001",
                "--host",
                "127.0.0.1",
                "--no-open-browser",
            ],
        )

        system, _ = configure_system()

        assert system.app_server.port == 9001
        assert system.app_server.host == "127.0.0.1"
        assert system.app_server.open_browser is False

    def test_defaults_apply_when_nothing_is_set(self, monkeypatch):
        for name in APP_SERVER_ENVIRONMENT:
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setattr("sys.argv", ["my_site.py"])

        system, modified = configure_system()

        assert system.app_server.port == DEFAULT_PORT
        assert system.app_server.host == "localhost"
        assert system.app_server.use_reloader is True
        assert system.app_server.open_browser is True
        assert modified["app_server"] == {}

    @pytest.mark.parametrize(
        "argv, field_name",
        [
            (["--no-reloader"], "use_reloader"),
            (["--no-open-browser"], "open_browser"),
            (["--no-inline-py"], "inline_py"),
            (["--no-serve-adjacent-files"], "serve_adjacent_files"),
        ],
    )
    def test_negative_flags_report_false(self, argv, field_name):
        assert parse_app_server(argv) == {field_name: False}


class TestFramedEnvironmentVariable:
    @pytest.mark.parametrize(
        "value, expected",
        [("false", False), ("0", False), ("no", False), ("true", True), ("1", True)],
    )
    def test_value_is_read_as_a_boolean(self, value, expected):
        # "false" used to be kept as text, which counts as true.
        parsed = ClientServerConfiguration.parse_env_variables(
            {"DRAFTER_FRAMED": value}
        )
        assert parsed["framed"] is expected


class TestConfigFiles:
    """Loading a config file used to end in RecursionError: reading the file
    went through Drafter's `open`, which asks for the configuration that is
    still being built."""

    def write_config(self, tmp_path, contents: dict):
        path = tmp_path / "drafter.json"
        path.write_text(json.dumps(contents), encoding="utf-8")
        return path

    def test_file_named_by_flag_is_loaded(self, tmp_path, monkeypatch):
        assert builtins.open is drafter_open

        path = self.write_config(
            tmp_path,
            {
                "app_server": {"port": 8456, "open_browser": False},
                "client_server": {"site_title": "From A File", "framed": False},
            },
        )
        monkeypatch.delenv("DRAFTER_CONFIG_FILE", raising=False)
        monkeypatch.setattr("sys.argv", ["my_site.py", "--config-file", str(path)])

        system, modified = configure_system()

        assert system.app_server.port == 8456
        assert system.app_server.open_browser is False
        assert system.client_server.site_title == "From A File"
        assert system.client_server.framed is False
        assert modified["app_server"]["port"] == 8456

    def test_file_named_by_environment_variable_is_loaded(self, tmp_path, monkeypatch):
        assert builtins.open is drafter_open

        path = self.write_config(tmp_path, {"app_server": {"port": 8457}})
        monkeypatch.setenv("DRAFTER_CONFIG_FILE", str(path))
        monkeypatch.setattr("sys.argv", ["my_site.py"])

        system, _ = configure_system()

        assert system.app_server.port == 8457
