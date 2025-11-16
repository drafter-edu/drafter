from dataclasses import dataclass
from functools import wraps
from typing import Any
import difflib

try:
    import bakery
except:
    bakery = None


@dataclass
class BakeryTestCase:
    args: tuple
    kwargs: dict
    result: Any
    line: int
    caller: str


DEFAULT_STACK_DEPTH = 7


def get_line_code(depth=DEFAULT_STACK_DEPTH):
    # Load in extract_stack, or provide shim for environments without it.
    try:
        from traceback import extract_stack

        trace = extract_stack()
        # Find the first assert_equal line
        for data in trace:
            line, code = data[1], data[3]
            if code.strip().startswith("assert_equal"):  # type: ignore
                return line, code
        # If none found, just try jumping up there and see what we can find
        frame = trace[len(trace) - depth]
        line = frame[1]
        code = frame[3]
        return line, code
    except Exception:
        # logger.error(f"Error getting line and code: {e}")
        return None, None


class BakeryTests:
    def __init__(self):
        self.tests = []

    def wrap_get_line_code(self, original_function):
        @wraps(original_function)
        def new_function(*args, **kwargs):
            # line, code = original_function(*args, **kwargs)
            # return line, code
            return get_line_code()

        return new_function

    def track_bakery_tests(self, original_function):
        if bakery is None:
            return original_function

        @wraps(original_function)
        def new_function(*args, **kwargs):
            line, code = get_line_code(6)
            result = original_function(*args, **kwargs)
            if line is None or code is None:
                line = -1
                code = "<Missing code>"
            self.tests.append(BakeryTestCase(args, kwargs, result, line, code))

            # Emit telemetry event for this test
            self._emit_test_event(BakeryTestCase(args, kwargs, result, line, code))

            return result

        return new_function

    def _emit_test_event(self, test_case: BakeryTestCase):
        """Emit a telemetry event for a test case."""
        try:
            from drafter.monitor.audit import log_data
            from drafter.monitor.events.tests import TestCaseEvent
            from drafter.payloads.kinds.page import Page

            # Only emit events for Page tests
            if len(test_case.args) == 2:
                given, expected = test_case.args
                if isinstance(expected, Page):
                    # Get string representations
                    given_str = repr(given)
                    expected_str = repr(expected)

                    # Generate diff if test failed
                    diff_html = ""
                    if not test_case.result:
                        try:
                            from drafter.history import format_page_content

                            DIFF_WRAP_WIDTH = 60
                            given_formatted, _ = format_page_content(
                                given, DIFF_WRAP_WIDTH
                            )
                            expected_formatted, _ = format_page_content(
                                expected, DIFF_WRAP_WIDTH
                            )
                            diff_html = diff_tests(
                                given_formatted,
                                expected_formatted,
                                "Your function returned",
                                "But the test expected",
                            )
                        except Exception:
                            pass

                    log_data(
                        TestCaseEvent(
                            line=test_case.line,
                            caller=test_case.caller,
                            passed=bool(test_case.result),
                            given=given_str,
                            expected=expected_str,
                            diff_html=diff_html,
                        ),
                        "testing.track_bakery_tests",
                    )
        except Exception:
            # Don't let telemetry errors break tests
            pass

    def emit_test_summary(self):
        """Emit a summary of all tests."""
        try:
            from drafter.monitor.audit import log_data
            from drafter.monitor.events.tests import TestSummaryEvent
            from drafter.payloads.kinds.page import Page

            # Count tests
            total = 0
            passed = 0
            for test_case in self.tests:
                if len(test_case.args) == 2:
                    given, expected = test_case.args
                    if isinstance(expected, Page):
                        total += 1
                        if test_case.result:
                            passed += 1

            if total > 0:
                log_data(
                    TestSummaryEvent(
                        total=total,
                        passed=passed,
                        failed=total - passed,
                    ),
                    "testing.emit_test_summary",
                )
        except Exception:
            pass


# Modifies Bakery's copy of assert_equal, and also provides a new version for folks who already imported
_bakery_tests = BakeryTests()
if bakery is not None:
    bakery.assertions.get_line_code = _bakery_tests.wrap_get_line_code(  # type: ignore
        bakery.assertions.get_line_code  # type: ignore
    )
    bakery.assert_equal = assert_equal = _bakery_tests.track_bakery_tests(
        bakery.assert_equal
    )
else:

    def assert_equal(*args, **kwargs):
        """Pointless definition of assert_equal to avoid errors"""
        print(
            "The Bakery testing library is not installed; skipping assert_equal tests. "
            "To fix this, you can install Bakery with 'pip install bakery' or use a different testing framework."
        )


DIFF_INDENT_WIDTH = 1
DIFF_WRAP_WIDTH = 60
differ = difflib.HtmlDiff(tabsize=DIFF_INDENT_WIDTH, wrapcolumn=DIFF_WRAP_WIDTH)


def diff_tests(left, right, left_name, right_name):
    """Compare two strings and show the differences in a table."""
    try:
        table = differ.make_table(
            left.splitlines(), right.splitlines(), left_name, right_name
        )
        return table
    except:
        if left == right:
            return "No differences found."
        return f"<pre>{left}</pre><pre>{right}</pre>"
