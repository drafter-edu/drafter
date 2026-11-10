"""Run the code from the "Use pytest or unittest" guide (drafter-edu/drafter#8).

The guide's listings are static fences spread over several files (a site
plus a test file per tool), which the docs fence harness does not execute.
This test extracts them by the file-name comment on their first line, writes
them to a temporary folder, and runs each tool for real in a subprocess, so
the guide cannot drift away from what actually works.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

GUIDE = Path(__file__).parent.parent / "docs" / "add" / "use-pytest-or-unittest.md"
SITE_FILE = "cookie_game.py"
PYTEST_FILE = "test_cookie_game.py"
UNITTEST_FILE = "check_cookie_game.py"

NAMED_FENCE = re.compile(
    r"^```python\n# (?P<name>[\w.]+\.py)\n(?P<body>.*?)^```$",
    re.MULTILINE | re.DOTALL,
)


def guide_listings() -> dict[str, str]:
    """Map each file name the guide shows to that file's code."""
    text = GUIDE.read_text(encoding="utf-8").replace("\r\n", "\n")
    return {
        match["name"]: f"# {match['name']}\n{match['body']}"
        for match in NAMED_FENCE.finditer(text)
    }


def write_listings(folder: Path, *names: str) -> None:
    listings = guide_listings()
    for name in names:
        (folder / name).write_text(listings[name], encoding="utf-8")


def run_in(folder: Path, *command: str) -> subprocess.CompletedProcess:
    """Run a command the way a student would: from the project folder, with
    no DRAFTER_SKIP already set (the guide's test files must set it)."""
    environment = {
        key: value for key, value in os.environ.items() if key != "DRAFTER_SKIP"
    }
    return subprocess.run(
        [sys.executable, *command],
        cwd=folder,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_guide_shows_all_three_files():
    assert set(guide_listings()) == {SITE_FILE, PYTEST_FILE, UNITTEST_FILE}


def test_pytest_listing_passes(tmp_path):
    write_listings(tmp_path, SITE_FILE, PYTEST_FILE)

    result = run_in(tmp_path, "-m", "pytest", "-q", "-p", "no:cacheprovider")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "3 passed" in result.stdout


def test_unittest_listing_passes(tmp_path):
    write_listings(tmp_path, SITE_FILE, UNITTEST_FILE)

    result = run_in(tmp_path, UNITTEST_FILE)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Ran 3 tests" in result.stderr
    assert "OK" in result.stderr


@pytest.mark.parametrize(
    "broken_line, fixed_line",
    [('"Your score is 7\\n",', '"Your score is 8\\n",')],
)
def test_pytest_reports_a_wrong_expectation(tmp_path, broken_line, fixed_line):
    """The failure output the guide quotes is what pytest really prints."""
    write_listings(tmp_path, SITE_FILE, PYTEST_FILE)
    test_file = tmp_path / PYTEST_FILE
    code = test_file.read_text(encoding="utf-8")
    assert broken_line in code
    test_file.write_text(code.replace(broken_line, fixed_line), encoding="utf-8")

    result = run_in(tmp_path, "-m", "pytest", "-q", "-p", "no:cacheprovider")

    assert result.returncode == 1
    assert "1 failed, 2 passed" in result.stdout
    assert "At index 1 diff: 'Your score is 7\\n' != 'Your score is 8\\n'" in (
        result.stdout
    )


def test_wrapped_drafter_assertion_fails_the_test(tmp_path):
    """`assert assert_has(...)` turns Drafter's False into a test failure."""
    write_listings(tmp_path, SITE_FILE, PYTEST_FILE)
    test_file = tmp_path / PYTEST_FILE
    code = test_file.read_text(encoding="utf-8")
    assert '"Your score is 12"' in code
    test_file.write_text(
        code.replace('"Your score is 12"', '"Your score is 99"'), encoding="utf-8"
    )

    result = run_in(tmp_path, "-m", "pytest", "-q", "-p", "no:cacheprovider")

    assert result.returncode == 1
    assert "1 failed, 2 passed" in result.stdout
    # Drafter's own explanation is part of the report.
    assert "Could not find 'Your score is 99'" in result.stdout
