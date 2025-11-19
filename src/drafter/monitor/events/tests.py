"""
Test status events for tracking student test results.
"""

from dataclasses import dataclass
from typing import Any, Optional

from drafter.monitor.events.base import BaseEvent


@dataclass
class TestCaseEvent(BaseEvent):
    """
    Event emitted for a single test case result.
    :ivar line: Line number where the test is located
    :ivar caller: The code that called the test
    :ivar passed: Whether the test passed
    :ivar given: String representation of what was given
    :ivar expected: String representation of what was expected
    :ivar given_formatted: Formatted version of the given value
    :ivar expected_formatted: Formatted version of the expected value
    :ivar diff_html: HTML diff showing the differences (if test failed)
    """

    line: int = -1
    caller: str = ""
    passed: bool = True
    given: str = ""
    expected: str = ""
    given_formatted: str = ""
    expected_formatted: str = ""
    diff_html: str = ""
    event_type: str = "TestCaseEvent"

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
            "diff_html": self.diff_html,
        }
