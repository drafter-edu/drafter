import sys
from dataclasses import dataclass
from functools import wraps
from typing import Any, Optional

import difflib
from drafter.monitor.audit import log_data
from drafter.monitor.events.tests import TestCaseEvent
from drafter.history.formatting import format_page_content
from drafter.ast_tools import get_all_relevant_lines

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


def try_getting_full_code(filename: str, lineno: int) -> Optional[str]:
    try:
        with open(filename, "r") as f:
            code = f.read()
            return get_all_relevant_lines(lineno, code)
    except Exception:
        return None


DEFAULT_STACK_DEPTH = 7


def get_line_code(target, depth=DEFAULT_STACK_DEPTH):
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
        # If none found, just try jumping up there and see what we can find
        frame = trace[len(trace) - depth]
        line = frame[1]
        code = frame[3]
        return line, code
    except Exception as e:
        print(e)
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
            return get_line_code("assert_")

        return new_function

    def track_bakery_tests(self, original_function):
        if bakery is None:
            return original_function

        @wraps(original_function)
        def new_function(*args, **kwargs):
            line, code = get_line_code("assert_")
            result = original_function(*args, **kwargs)
            if line is None or code is None:
                line = -1
                code = "<Missing code>"
            self.tests.append(BakeryTestCase(args, kwargs, result, line, code))
            try:
                self._emit_test_event(BakeryTestCase(args, kwargs, result, line, code))
            except Exception as e:
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
                    "Actually Returned",
                    "Test Expected",
                )
            )
            # print(diff_html)

        log_data(
            TestCaseEvent(
                line=test_case.line,
                caller=test_case.caller,
                passed=bool(test_case.result),
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


def assert_has(page_content: str, expected_text: str, message: str = "") -> bool:
    """
    Assert that the page content contains the expected text.
    
    Args:
        page_content: The full page HTML content to search in
        expected_text: The text that should be present in the page
        message: Optional custom error message
        
    Returns:
        True if assertion passes, False otherwise
        
    Example:
        assert_has(page.render(), "Welcome")
        assert_has(page.render(), "Hello, World!", "Homepage should greet user")
    """
    if expected_text in page_content:
        return True
    else:
        error_msg = message or f"Expected to find '{expected_text}' in page content"
        print(f"AssertionError: {error_msg}")
        return False


def assert_in(expected_text: str, page_content: str, message: str = "") -> bool:
    """
    Assert that the expected text is in the page content.
    Alternative to assert_has with reversed parameter order.
    
    Args:
        expected_text: The text that should be present in the page
        page_content: The full page HTML content to search in
        message: Optional custom error message
        
    Returns:
        True if assertion passes, False otherwise
        
    Example:
        assert_in("Welcome", page.render())
        assert_in("Hello, World!", page.render(), "Homepage should greet user")
    """
    return assert_has(page_content, expected_text, message)


def assert_state(state: Any, expected_fields: dict, message: str = "") -> bool:
    """
    Assert that the state object has the expected field values.
    
    Args:
        state: The state object to check (can be dict or object with attributes)
        expected_fields: Dictionary of field names to expected values
        message: Optional custom error message
        
    Returns:
        True if all assertions pass, False otherwise
        
    Example:
        assert_state(state, {'count': 5, 'name': 'Alice'})
        assert_state(state, {'logged_in': True}, "User should be logged in")
    """
    all_passed = True
    
    for field_name, expected_value in expected_fields.items():
        # Try dictionary access first, then attribute access
        try:
            if isinstance(state, dict):
                actual_value = state.get(field_name)
            else:
                actual_value = getattr(state, field_name, None)
            
            if actual_value != expected_value:
                error_msg = message or f"Expected state.{field_name} to be {expected_value!r}, but got {actual_value!r}"
                print(f"AssertionError: {error_msg}")
                all_passed = False
        except (KeyError, AttributeError) as e:
            error_msg = message or f"Field '{field_name}' not found in state"
            print(f"AssertionError: {error_msg}")
            all_passed = False
    
    return all_passed
