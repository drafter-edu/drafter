"""Tests for presenting student-facing errors in the terminal.

When a StudentFacingError escapes on the host (the port is in use, the
main file cannot be found), there is no browser error page to show it in.
start_server prints the friendly title, explanation, numbered steps, and a
"Details" line instead of a traceback and exits with status 1; the verbose
setting restores the traceback by letting the exception propagate.
"""

import pytest

from drafter import launch
from drafter.app import app_server
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.data.errors import (
    DEFAULT_TERMINAL_ERROR_TITLE,
    TERMINAL_WIDTH,
    StudentFacingError,
    format_student_facing_error,
)


def full_error() -> StudentFacingError:
    return StudentFacingError(
        "Port 8000 is already in use by another program.",
        title="Port already in use",
        friendly=(
            "You asked Drafter to use port 8000, but another program on your "
            "computer is already using it, so Drafter cannot listen there."
        ),
        steps=(
            "Stop the other program: press Ctrl+C in its terminal or open "
            "http://localhost:8000/--stop-server in your browser.",
            "Or run your program with a different port, such as --port 8001.",
        ),
    )


class TestFormatStudentFacingError:
    def test_lays_out_title_explanation_steps_and_details(self):
        text = format_student_facing_error(full_error())
        lines = text.split("\n")

        assert lines[0] == ""
        assert lines[1] == "=" * TERMINAL_WIDTH
        assert lines[2] == "Port already in use"
        assert lines[3] == "=" * TERMINAL_WIDTH
        assert lines[4].startswith("You asked Drafter to use port 8000")
        assert "What to try:" in lines
        assert any(line.startswith("  1. Stop the other program") for line in lines)
        assert any(line.startswith("  2. Or run your program") for line in lines)
        assert any(line.startswith("Details: Port 8000 is already") for line in lines)
        assert lines[-1] == ""

    def test_wraps_long_lines_to_the_terminal_width(self):
        text = format_student_facing_error(full_error())
        assert all(len(line) <= TERMINAL_WIDTH for line in text.split("\n"))

    def test_continuation_lines_of_a_step_are_indented_under_its_text(self):
        lines = format_student_facing_error(full_error()).split("\n")
        first_step = lines.index(
            next(line for line in lines if line.startswith("  1. "))
        )
        assert lines[first_step + 1].startswith("     ")

    def test_falls_back_to_message_and_default_title(self):
        text = format_student_facing_error(StudentFacingError("Something broke."))
        assert DEFAULT_TERMINAL_ERROR_TITLE in text
        assert "Something broke." in text
        assert "What to try:" not in text
        assert "Details:" not in text


class TestStartServerPresentsHostErrors:
    @pytest.fixture
    def failing_server(self, monkeypatch):
        def fail(system, server, initial_state):
            raise full_error()

        monkeypatch.setattr(launch, "is_web", lambda: False)
        monkeypatch.setattr(app_server, "serve_app_once", fail)
        # Build the configuration by hand rather than from the process: the
        # real one reads sys.argv, so running `pytest --verbose` would turn on
        # Drafter's own verbose setting and change the behavior under test.
        system = SystemConfiguration(
            bootstrap=BootstrapConfiguration(path="main.py"),
            client_server=ClientServerConfiguration(),
            app_server=AppServerConfiguration(),
            app_builder=AppBuilderConfiguration(),
            app_common=AppCommonConfiguration(),
        )
        monkeypatch.setattr(launch, "get_system_configuration", lambda: system)
        return system

    def test_prints_explanation_and_exits_with_status_one(self, failing_server, capsys):
        with pytest.raises(SystemExit) as excinfo:
            launch.start_server(open_browser=False, argv=[])

        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Port already in use" in captured.err
        assert "What to try:" in captured.err
        assert "Traceback" not in captured.err
        assert captured.out == ""

    def test_verbose_lets_the_error_propagate(self, failing_server):
        with pytest.raises(StudentFacingError):
            launch.start_server(open_browser=False, verbose=True, argv=[])
