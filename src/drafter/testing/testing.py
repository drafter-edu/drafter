"""Integration with the Bakery testing library.

Importing this module patches Bakery (when installed) so that every
`assert_equal` call is recorded as a `BakeryTestCase` and emitted as a
`TestCaseEvent` for display in Drafter's debug and testing panels. When
Bakery is not installed, a stub `assert_equal` is provided that simply
prints a warning.
"""

import difflib
import os
import sys
from dataclasses import dataclass
from functools import wraps
from typing import Any

from drafter.data.details.tests import TestCaseEvent
from drafter.helpers.ast_tools import get_all_relevant_lines
from drafter.history.formatting import format_page_content
from drafter.monitor.audit import log_record

try:
    import bakery
except:  # noqa: E722
    bakery = None


@dataclass
class BakeryTestCase:
    """Records a single test case execution result.

    Attributes:
        args: Positional arguments passed to the test function.
        kwargs: Keyword arguments passed to the test function.
        result: The result or return value from the test function.
        line: The line number in the source file where the test was called.
        caller: The source code snippet of the assertion call, extracted
            from the call stack (or a placeholder if unavailable).
        kind: The type of assertion (e.g., 'assert_equal', 'assert_state').
    """

    args: tuple
    kwargs: dict
    result: Any
    line: int
    caller: str
    kind: str


def try_getting_full_code(filename: str, lineno: int) -> str | None:
    """Retrieve the full multi-line code for a test from source file.

    Args:
        filename: The path to the source file.
        lineno: The line number to extract code from.

    Returns:
        The full code snippet as a string, or None if retrieval fails.
    """
    try:
        with open(filename) as f:
            code = f.read()
            return get_all_relevant_lines(lineno, code)
    except Exception:
        return None


UNKNOWN_TEST_CODE = "<unknown test code>"
"""Stands in for an assertion's source text when Python cannot read the
file it was written in (code typed at a prompt or passed with `-c`)."""


def _testing_package_directories() -> tuple[str, ...]:
    """Folders holding Drafter's (and Bakery's) own code.

    A frame from one of these is part of the assertion machinery, never
    the student's test.
    """
    import drafter

    packages = [drafter] if bakery is None else [drafter, bakery]
    files = [getattr(package, "__file__", None) for package in packages]
    return tuple(
        os.path.dirname(os.path.abspath(file))
        for file in files
        if isinstance(file, str)
    )


def _is_inside(filename: str, directories: tuple[str, ...]) -> bool:
    """Whether a stack frame's file is in one of the given folders."""
    path = os.path.normcase(os.path.abspath(filename))
    return any(
        path.startswith(os.path.normcase(directory) + os.sep)
        for directory in directories
    )


def get_line_code(target):
    """Extract source code line and its context for a test assertion.

    Searches the call stack for a line that starts with the target string
    and retrieves the full multi-line code snippet. An assertion does not
    always start its line (`ok = assert_equal(...)`, or one written after
    `if ...:`), and sometimes the source cannot be read at all, so the
    search falls back to the innermost frame outside Drafter's own code:
    the line that called the assertion.

    Args:
        target: The string to search for in the call stack (e.g., 'assert_').

    Returns:
        A tuple of (line_number, code_string), or (None, None) if not found.
    """
    # Load in extract_stack, or provide shim for environments without it.
    try:
        from traceback import extract_stack

        trace = extract_stack()
        # Find the first assert_equal line
        for data in trace:
            filename, line, code = data[0], data[1], data[3]
            if line is None or code is None:
                continue
            if code.strip().startswith(target):  # type: ignore
                possible_full_line = try_getting_full_code(filename, line)
                if possible_full_line is not None:
                    code = possible_full_line
                return line, code

        # No line starts with the target, so report the caller: the
        # innermost frame that is not part of the assertion machinery.
        own_directories = _testing_package_directories()
        for data in reversed(trace):
            filename, line, code = data[0], data[1], data[3]
            if line is None or _is_inside(filename, own_directories):
                continue
            full_code = try_getting_full_code(filename, line)
            return line, full_code or code or UNKNOWN_TEST_CODE
        return None, None
    except Exception as e:
        print(e)
        # logger.error(f"Error getting line and code: {e}")
        return None, None


class BakeryTests:
    """Tracks and emits test case events from Bakery test assertions.

    This class wraps Bakery test functions to capture test results,
    source code context, and emit telemetry events for test execution.
    """

    def __init__(self):
        self.tests = []

    def wrap_get_line_code(self, original_function):
        """Replace Bakery's `get_line_code` with Drafter's implementation.

        The returned wrapper ignores the original function and its
        arguments entirely, delegating to this module's `get_line_code` to
        search the call stack for a line starting with `assert_`.

        Args:
            original_function: Bakery's original `get_line_code`, used only
                for its metadata (via `functools.wraps`).

        Returns:
            The replacement function.
        """

        @wraps(original_function)
        def new_function(*args, **kwargs):
            # line, code = original_function(*args, **kwargs)
            # return line, code
            return get_line_code("assert_")

        return new_function

    def track_bakery_tests(self, original_function):
        """Wrap a Bakery assertion so that each call is recorded and reported.

        The returned wrapper captures the calling source line, runs the
        original assertion, appends a `BakeryTestCase` to `self.tests`, and
        emits a `TestCaseEvent` (errors during emission are printed rather
        than raised).

        Args:
            original_function: The assertion function (e.g., Bakery's
                `assert_equal`) to instrument.

        Returns:
            The instrumented function, or `original_function` unchanged
            when Bakery is not installed.
        """
        if bakery is None:
            return original_function

        @wraps(original_function)
        def new_function(*args, **kwargs):
            line, code = get_line_code("assert_")
            result = original_function(*args, **kwargs)
            if line is None or code is None:
                line = -1
                code = "<Missing code>"
            test_case = BakeryTestCase(
                args, kwargs, result, line, code, kind="assert_equal"
            )
            self.tests.append(test_case)
            try:
                self._emit_test_event(test_case)
            except Exception as e:
                # TODO: Do something better here
                print(f"Error emitting test event: {e}")
            return result

        return new_function

    def _emit_test_event(self, test_case: BakeryTestCase):
        """Emit a test case event to the main event bus."""
        if len(test_case.args) >= 2:
            expected = test_case.args[0]
            actual = test_case.args[1]
        elif len(test_case.args) == 1:
            expected = test_case.args[0]
            actual = None
        else:
            expected = None
            actual = None

        actual_str = repr(actual)
        expected_str = repr(expected)

        diff_html = ""
        actual_formatted = format_page_content(actual, escape=False)
        expected_formatted = format_page_content(expected, escape=False)
        if not test_case.result:
            diff_html = "".join(
                difflib.unified_diff(
                    actual_formatted.splitlines(keepends=True),
                    expected_formatted.splitlines(keepends=True),
                    "Test Expected",
                    "Actually Returned",
                )
            )
            # print(diff_html)

        log_record(
            TestCaseEvent(
                line=test_case.line,
                caller=test_case.caller,
                passed=bool(test_case.result),
                assertion_kind=test_case.kind,
                given=actual_str,
                expected=expected_str,
                given_formatted=actual_formatted,
                expected_formatted=expected_formatted,
                diff_html=diff_html,
            ),
            "testing.track_bakery_tests",
        )


# Modifies Bakery's copy of assert_equal, and also provides a new version for folks who already imported
_bakery_tests = BakeryTests()
if bakery is not None:
    bakery.assertions.get_line_code = _bakery_tests.wrap_get_line_code(  # type: ignore
        bakery.assertions.get_line_code  # type: ignore
    )
    bakery.assert_equal = assert_equal = _bakery_tests.track_bakery_tests(
        bakery.assert_equal
    )
    if "__main__" in sys.modules:
        if hasattr(sys.modules["__main__"], "assert_equal"):
            sys.modules["__main__"].assert_equal = assert_equal  # type: ignore
else:

    def assert_equal(*args, **kwargs):
        """Pointless definition of assert_equal to avoid errors"""
        print(
            "The Bakery testing library is not installed; skipping assert_equal tests. "
            "To fix this, you can install Bakery with 'pip install bakery' or use a different testing framework."
        )
