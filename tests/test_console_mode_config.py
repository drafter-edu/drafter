"""Tests for the client_server `console_mode` configuration setting.

The setting controls where captured print() output (and the Python REPL)
appears in the browser: "auto" (footer console in debug mode), "hover"
(floating box), "toast" (corner toasts), or "devtools" (browser console
only). The value itself is consumed by the JS side; these tests cover the
Python configuration pipeline: defaults, environment variables, CLI parsing,
serialization, and copying.
"""

import argparse

import pytest

from drafter.config.client_server import ClientServerConfiguration


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    ClientServerConfiguration.extend_parser(parser)
    return parser


class TestConsoleModeDefaults:
    def test_default_is_auto(self):
        config = ClientServerConfiguration()
        assert config.console_mode == "auto"

    def test_to_json_includes_console_mode(self):
        config = ClientServerConfiguration(console_mode="hover")
        assert config.to_json()["console_mode"] == "hover"

    def test_copy_preserves_console_mode(self):
        config = ClientServerConfiguration(console_mode="toast")
        assert config.copy().console_mode == "toast"


class TestConsoleModeEnvVars:
    def test_env_var_parsed(self):
        result = ClientServerConfiguration.parse_env_variables(
            {"DRAFTER_CONSOLE_MODE": "hover"}
        )
        assert result["console_mode"] == "hover"

    def test_env_var_absent(self):
        result = ClientServerConfiguration.parse_env_variables({})
        assert "console_mode" not in result


class TestConsoleModeCli:
    @pytest.mark.parametrize("mode", ["auto", "hover", "toast", "devtools"])
    def test_console_mode_flag(self, mode):
        parser = make_parser()
        parsed, _ = parser.parse_known_args(["--console-mode", mode])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert result["console_mode"] == mode

    def test_console_mode_not_given(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args([])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert "console_mode" not in result

    def test_invalid_console_mode_rejected(self):
        parser = make_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--console-mode", "everywhere"])

    def test_merges_into_configuration(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args(["--console-mode", "devtools"])
        config = ClientServerConfiguration()
        config.merge_in_args(
            ClientServerConfiguration.parse_args(vars(parsed)), False
        )
        assert config.console_mode == "devtools"
