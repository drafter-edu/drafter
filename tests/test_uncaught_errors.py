"""Tests for how a Drafter error at the top of a program is shown.

`add_website_file("missing.txt")` near the top of a file used to end in a
raw traceback, so its explanation and "Did you mean" steps were never
seen. Drafter now installs an excepthook (on the computer only) that
prints the same titled box `start_server` uses for its own errors.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from drafter.data.errors import StudentFacingError, format_student_facing_error
from drafter.helpers import uncaught_errors
from drafter.helpers.uncaught_errors import (
    find_student_location,
    install_student_error_hook,
    make_student_error_hook,
)

REPOSITORY = Path(__file__).resolve().parent.parent


def raised(error: BaseException) -> tuple:
    """The (type, value, traceback) triple Python hands an excepthook."""
    try:
        raise error
    except BaseException as caught:
        return type(caught), caught, caught.__traceback__


def student_error() -> StudentFacingError:
    return StudentFacingError(
        "add_website_file: file not found: 'wordz.txt'",
        title="Website File Not Found",
        friendly="Drafter looked for a file named 'wordz.txt'.",
        steps=("Did you mean 'words.txt'?",),
    )


@pytest.fixture
def quiet(monkeypatch):
    """Run with the verbose setting off, whatever the test session uses."""
    monkeypatch.setattr(uncaught_errors, "wants_tracebacks", lambda: False)


class TestHook:
    def test_student_error_prints_the_box_and_no_traceback(self, quiet, capsys):
        previous_calls = []
        hook = make_student_error_hook(lambda *args: previous_calls.append(args))

        hook(*raised(student_error()))

        printed = capsys.readouterr().err
        assert "Website File Not Found" in printed
        assert "Did you mean 'words.txt'?" in printed
        assert "Traceback" not in printed
        assert previous_calls == []

    def test_box_says_where_in_the_program(self, quiet, capsys):
        hook = make_student_error_hook(lambda *args: None)

        hook(*raised(student_error()))

        assert "Where: test_uncaught_errors.py, line " in capsys.readouterr().err

    def test_other_errors_go_to_the_previous_hook(self, quiet, capsys):
        previous_calls = []
        hook = make_student_error_hook(lambda *args: previous_calls.append(args))
        triple = raised(KeyError("score"))

        hook(*triple)

        assert previous_calls == [triple]
        assert capsys.readouterr().err == ""

    def test_verbose_setting_keeps_the_traceback(self, monkeypatch, capsys):
        monkeypatch.setattr(uncaught_errors, "wants_tracebacks", lambda: True)
        previous_calls = []
        hook = make_student_error_hook(lambda *args: previous_calls.append(args))

        hook(*raised(student_error()))

        assert len(previous_calls) == 1
        assert capsys.readouterr().err == ""


class TestInstall:
    def test_installs_once(self, monkeypatch):
        def original(*args):
            """Stands in for whatever hook was there before."""

        monkeypatch.setattr(sys, "excepthook", original)

        install_student_error_hook()
        installed = sys.excepthook
        install_student_error_hook()

        assert installed is not original
        assert sys.excepthook is installed


class TestLocation:
    def test_names_the_innermost_frame_outside_drafter(self):
        _, _, error_traceback = raised(student_error())

        location = find_student_location(error_traceback)

        assert location.startswith("test_uncaught_errors.py, line ")

    def test_skips_frames_inside_drafter(self):
        from drafter import Header

        try:
            Header("Title", 9)
        except StudentFacingError as error:
            location = find_student_location(error.__traceback__)

        # Not text.py, where the error was raised.
        assert location.startswith("test_uncaught_errors.py, line ")

    def test_no_traceback_gives_no_location(self):
        assert find_student_location(None) == ""


class TestFormatting:
    def test_location_line_sits_under_the_title(self):
        text = format_student_facing_error(student_error(), "main.py, line 3")

        lines = text.splitlines()
        assert lines[4] == "Where: main.py, line 3"
        assert "Where:" not in format_student_facing_error(student_error())


class TestRealProgram:
    """Run an actual file the way a student does."""

    def run_program(self, tmp_path: Path, source: str) -> subprocess.CompletedProcess:
        (tmp_path / "main.py").write_text(source, encoding="utf-8")
        (tmp_path / "words.txt").write_text("apple\n", encoding="utf-8")
        environment = dict(os.environ, DRAFTER_SKIP="1")
        environment["PYTHONPATH"] = str(REPOSITORY / "src")
        environment.pop("DRAFTER_VERBOSE", None)
        return subprocess.run(
            [sys.executable, "main.py"],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_missing_website_file_shows_the_box(self, tmp_path):
        result = self.run_program(
            tmp_path,
            "from drafter import *\n\nadd_website_file('wordz.txt')\nstart_server()\n",
        )

        assert result.returncode == 1
        assert "Website File Not Found" in result.stderr
        assert "Did you mean 'words.txt'?" in result.stderr
        assert "Where: main.py, line 3" in result.stderr
        assert "Traceback" not in result.stderr

    def test_ordinary_error_still_shows_a_traceback(self, tmp_path):
        result = self.run_program(
            tmp_path, "from drafter import *\n\nscore = 1 / 0\nstart_server()\n"
        )

        assert result.returncode == 1
        assert "Traceback" in result.stderr
        assert "ZeroDivisionError" in result.stderr
