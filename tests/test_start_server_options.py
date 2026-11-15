"""Tests for the warnings `start_server` gives about how it was called.

A misspelled keyword such as `sight_title` used to be dropped without a
word. It now produces a warning (the site still starts), and a keyword
that only matches a method name no longer overwrites that method.

Statements written after `start_server(...)` get a warning too: they do
run, but only once the server stops on the computer, and straight after
the first page in the browser.
"""

from unittest.mock import MagicMock

import pytest

import drafter.launch
from drafter.client_server.client_server import ClientServer
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.configuration import (
    _reset_system_for_testing,
    _set_system_for_testing,
)
from drafter.data.telemetry import ErrorRecord
from drafter.launch import (
    CODE_AFTER_START_ERROR_ID,
    LEGACY_START_SERVER_OPTIONS,
    UNKNOWN_OPTION_ERROR_ID,
    describe_unknown_option,
    find_code_after_call,
    find_unknown_options,
    start_server,
)


def make_system() -> SystemConfiguration:
    return SystemConfiguration(
        bootstrap=BootstrapConfiguration(path="main.py"),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(),
        app_common=AppCommonConfiguration(),
    )


@pytest.fixture
def system():
    """Inject a fresh SystemConfiguration and reset it afterwards."""
    fresh = make_system()
    _set_system_for_testing(fresh)
    yield fresh
    _reset_system_for_testing()


@pytest.fixture
def server(monkeypatch):
    """A server for `start_server` to use, with nothing actually served."""
    instance = ClientServer(custom_name="START_SERVER_OPTIONS_TEST")
    monkeypatch.setattr(drafter.launch, "get_main_server", lambda: instance)
    monkeypatch.setattr("drafter.app.app_server.serve_app_once", MagicMock())
    return instance


def warnings_on(server: ClientServer) -> list[ErrorRecord]:
    """The unknown-option warnings waiting on a server's event bus."""
    return [
        event
        for event in server.event_bus.unprocessed_events
        if event.kind == UNKNOWN_OPTION_ERROR_ID
    ]


class TestFindUnknownOptions:
    def test_real_settings_are_known(self, system):
        options = {"site_title": "Pets", "port": 8001, "zip_output": True}

        assert find_unknown_options(options, system.setting_names()) == []

    def test_misspelled_setting_is_unknown(self, system):
        options = {"sight_title": "Pets", "theme": "water"}

        assert find_unknown_options(options, system.setting_names()) == ["sight_title"]

    @pytest.mark.parametrize("name", sorted(LEGACY_START_SERVER_OPTIONS))
    def test_drafter_1_options_stay_quiet(self, system, name):
        assert find_unknown_options({name: "x"}, system.setting_names()) == []

    def test_legacy_options_are_not_real_settings(self, system):
        # A name that became a real setting should leave the legacy list.
        assert not LEGACY_START_SERVER_OPTIONS & system.setting_names()


class TestDescribeUnknownOption:
    def test_suggests_the_closest_setting(self, system):
        message = describe_unknown_option("sight_title", system.setting_names())

        assert message == (
            "Unknown start_server option 'sight_title'. Did you mean 'site_title'?"
        )

    def test_suggests_a_start_server_parameter(self, system):
        message = describe_unknown_option("inital_state", system.setting_names())

        assert message.endswith("Did you mean 'initial_state'?")

    def test_no_suggestion_when_nothing_is_close(self, system):
        message = describe_unknown_option("zzzzqqqq", system.setting_names())

        assert message == "Unknown start_server option 'zzzzqqqq'."


class TestStartServerOnTheComputer:
    def test_warning_is_printed_and_the_site_still_starts(self, system, server, capsys):
        start_server(sight_title="Pets")

        captured = capsys.readouterr()
        assert (
            "Warning: Unknown start_server option 'sight_title'. "
            "Did you mean 'site_title'? The option was ignored."
        ) in captured.err
        drafter.app.app_server.serve_app_once.assert_called_once()

    def test_known_options_print_nothing(self, system, server, capsys):
        start_server(site_title="Pets", reloader=False, src_image_folder="images")

        assert capsys.readouterr().err == ""
        assert system.client_server.site_title == "Pets"

    def test_method_name_does_not_overwrite_the_method(self, system, server, capsys):
        """`start_server(copy=5)` used to replace the settings' `copy` method."""
        start_server(copy=5)

        assert callable(system.client_server.copy)
        assert callable(system.bootstrap.copy)
        assert "Unknown start_server option 'copy'" in capsys.readouterr().err


class TestStartServerInTheBrowser:
    @pytest.fixture(autouse=True)
    def in_the_browser(self, monkeypatch):
        monkeypatch.setattr(drafter.launch, "is_web", lambda: True)
        monkeypatch.setattr("drafter.bridge.run_client_bridge", MagicMock())

    def test_warning_goes_to_the_debug_panel(self, system, server, capsys):
        start_server(sight_title="Pets")

        (warning,) = warnings_on(server)
        assert warning.error is not None
        assert warning.error.severity == "warning"
        assert warning.error.friendly_title == "Unknown start_server Option"
        assert "'sight_title'" in warning.error.friendly_message
        assert warning.error.friendly_steps[0] == (
            "Change 'sight_title' to 'site_title' in your start_server(...) call."
        )
        # The page's console is for the student's own printing.
        assert capsys.readouterr().err == ""

    def test_no_warning_for_known_options(self, system, server):
        start_server(site_title="Pets", style="skeleton")

        assert warnings_on(server) == []


class TestFindCodeAfterCall:
    def test_call_on_the_last_line(self):
        source = "from drafter import *\n\nstart_server()\n"

        assert find_code_after_call(source, 3) is None

    def test_statement_after_the_call(self):
        source = "from drafter import *\nstart_server()\n\nprint('done')\n"

        assert find_code_after_call(source, 2) == 4

    def test_comments_and_blank_lines_are_not_code(self):
        source = "start_server()\n\n# The end.\n"

        assert find_code_after_call(source, 1) is None

    def test_call_written_over_several_lines(self):
        source = "start_server(\n    0,\n    site_title='Pets',\n)\nx = 1\n"

        assert find_code_after_call(source, 3) == 5

    def test_call_under_a_main_guard(self):
        source = "if __name__ == '__main__':\n    start_server()\nx = 1\n"

        assert find_code_after_call(source, 2) == 3

    def test_call_inside_a_function_is_not_judged(self):
        source = "def main():\n    start_server()\n\nmain()\n"

        assert find_code_after_call(source, 2) is None


class TestCodeAfterStartServer:
    def run_file(self, tmp_path, source: str) -> None:
        """Run a program file the way Python runs a student's main file."""
        main_file = tmp_path / "main.py"
        main_file.write_text(source, encoding="utf-8")
        code = compile(source, str(main_file), "exec")
        exec(code, {"__name__": "__main__", "start_server": start_server})

    def test_terminal_warning_names_the_file_and_line(
        self, system, server, tmp_path, capsys
    ):
        self.run_file(tmp_path, "start_server()\n\nscore = 5\n")

        printed = capsys.readouterr().err
        assert (
            "Warning: main.py has code after start_server(...), starting on line 3."
        ) in printed
        assert "will not run until the server stops" in printed

    def test_no_warning_when_start_server_is_last(
        self, system, server, tmp_path, capsys
    ):
        self.run_file(tmp_path, "score = 5\nstart_server()\n# The end.\n")

        assert capsys.readouterr().err == ""

    def test_browser_warning_goes_to_the_debug_panel(
        self, system, server, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(drafter.launch, "is_web", lambda: True)
        monkeypatch.setattr("drafter.bridge.run_client_bridge", MagicMock())

        self.run_file(tmp_path, "start_server()\nscore = 5\n")

        (warning,) = [
            event
            for event in server.event_bus.unprocessed_events
            if event.kind == CODE_AFTER_START_ERROR_ID
        ]
        assert warning.error.severity == "warning"
        assert warning.error.friendly_title == "Code After start_server"
        assert "Line 2 of main.py" in warning.error.friendly_message
        assert "last line" in warning.error.friendly_steps[0]

    def test_code_that_is_not_in_a_file_is_skipped(self, system, server, capsys):
        code = compile("start_server()\nscore = 5\n", "<string>", "exec")

        exec(code, {"start_server": start_server})

        assert capsys.readouterr().err == ""

    def test_program_known_only_to_linecache_is_still_checked(
        self, system, server, monkeypatch
    ):
        """The browser runs the program under a name that is not a real path."""
        import linecache

        monkeypatch.setattr(drafter.launch, "is_web", lambda: True)
        monkeypatch.setattr("drafter.bridge.run_client_bridge", MagicMock())
        source = "start_server()\nscore = 5\n"
        name = "browser_main_for_test.py"
        monkeypatch.setitem(
            linecache.cache,
            name,
            (len(source), None, source.splitlines(keepends=True), name),
        )

        exec(compile(source, name, "exec"), {"start_server": start_server})

        warnings = [
            event
            for event in server.event_bus.unprocessed_events
            if event.kind == CODE_AFTER_START_ERROR_ID
        ]
        assert len(warnings) == 1
        assert (
            "Line 2 of browser_main_for_test.py" in warnings[0].error.friendly_message
        )
