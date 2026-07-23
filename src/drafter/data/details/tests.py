"""
Test status events for tracking student test results.
"""

from dataclasses import dataclass
from typing import Any

from drafter.data.telemetry import TelemetryRecord


@dataclass
class TestCaseEvent(TelemetryRecord):
    """
    Event emitted for a single test case result.

    Attributes:
        line: Line number where the test is located
        caller: The code that called the test
        passed: Whether the test passed
        given: String representation of what was given
        expected: String representation of what was expected
        given_formatted: Formatted version of the given value
        expected_formatted: Formatted version of the expected value
        assertion_kind: The type of assertion (e.g., 'assert_equal', 'assert_state')
        diff_html: HTML diff showing the differences (if test failed)
    """

    line: int = -1
    caller: str = ""
    passed: bool = True
    given: str = ""
    expected: str = ""
    given_formatted: str = ""
    expected_formatted: str = ""
    diff_html: str = ""
    assertion_kind: str = "assert_equal"
    kind: str = "TestCaseEvent"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "line": self.line,
            "caller": self.caller,
            "passed": self.passed,
            "given": self.given,
            "expected": self.expected,
            "given_formatted": self.given_formatted,
            "expected_formatted": self.expected_formatted,
            "assertion_kind": self.assertion_kind,
            "diff_html": self.diff_html,
        }
