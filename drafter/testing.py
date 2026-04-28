from dataclasses import dataclass, is_dataclass, fields as dataclass_fields
from functools import wraps
from typing import Any
import difflib
try:
    import bakery
except:
    bakery = None

import logging
logger = logging.getLogger('drafter')

@dataclass
class BakeryTestCase:
    args: tuple
    kwargs: dict
    result: Any
    line: int
    caller: str


DEFAULT_STACK_DEPTH = 7
def get_line_code(depth = DEFAULT_STACK_DEPTH):
    # Load in extract_stack, or provide shim for environments without it.
    try:
        from traceback import extract_stack
        trace = extract_stack()
        # Find the first assert_equal line
        for data in trace:
            line, code = data[1], data[3]
            if code.strip().startswith('assert_equal'):
                return line, code
        # If none found, just try jumping up there and see what we can find
        frame = trace[len(trace) - depth]
        line = frame[1]
        code = frame[3]
        return line, code
    except Exception as e:
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
            self.tests.append(BakeryTestCase(args, kwargs, result, line, code))
            return result

        return new_function


# Modifies Bakery's copy of assert_equal, and also provides a new version for folks who already imported
_bakery_tests = BakeryTests()
if bakery is not None:
    bakery.assertions.get_line_code = _bakery_tests.wrap_get_line_code(bakery.assertions.get_line_code)
    bakery.assert_equal = assert_equal = _bakery_tests.track_bakery_tests(bakery.assert_equal)
else:
    def assert_equal(*args, **kwargs):
        """ Pointless definition of assert_equal to avoid errors """
        print("The Bakery testing library is not installed; skipping assert_equal tests. "
              "To fix this, you can install Bakery with 'pip install bakery' or use a different testing framework.")


DIFF_INDENT_WIDTH = 1
DIFF_WRAP_WIDTH = 60
differ = difflib.HtmlDiff(tabsize=DIFF_INDENT_WIDTH, wrapcolumn=DIFF_WRAP_WIDTH)

def diff_tests(left, right, left_name, right_name):
    """ Compare two strings and show the differences in a table. """
    try:
        table = differ.make_table(left.splitlines(), right.splitlines(), left_name, right_name)
        return table
    except:
        if left == right:
            return "No differences found."
        return f"<pre>{left}</pre><pre>{right}</pre>"


# ---------------------------------------------------------------------------
# assert_page helpers
# ---------------------------------------------------------------------------

SIMPLE_PRIMITIVE_TYPES = (str, int, float, bool)
_STYLE_KEY_PREFIX = 'style_'

# Bakery message templates (duplicated here so they work even if bakery is
# unavailable at import time).
_MSG_LINE_CODE = " - [line {line}] {code}"
_MSG_FAILURE = "FAILURE{context}, predicted answer was {y}, computed answer was {x}."
_MSG_SUCCESS = "TEST PASSED{context}"
_MSG_UNRELATED = (
    "FAILURE{context}, predicted answer was {y} ({y_type!r}), "
    "computed answer was {x} ({x_type!r}). "
    "You attempted to compare unrelated data types.")


def _filter_non_style_settings(settings: dict) -> dict:
    """Return a copy of *settings* with all ``style_*`` keys removed."""
    return {k: v for k, v in settings.items() if not k.startswith(_STYLE_KEY_PREFIX)}


def _get_assert_page_line_code():
    """Return the (line, code) of the nearest ``assert_page`` call in the stack."""
    try:
        from traceback import extract_stack
        trace = extract_stack()
        for frame in trace:
            code = frame[3]
            if code and code.strip().startswith('assert_page'):
                return frame[1], code
        # Fallback: just return the outermost user frame
        frame = trace[max(0, len(trace) - 5)]
        return frame[1], frame[3]
    except Exception:
        return None, None


def _page_report(left, right, context_path: str, line, code) -> bool:
    """
    Compare *left* and *right* using ``==`` and print a bakery-style message.
    Updates ``bakery.assertions.student_tests`` when bakery is available.
    Returns ``True`` on success, ``False`` on failure.
    """
    # Build the context string
    context = ""
    if None not in (line, code):
        context = _MSG_LINE_CODE.format(line=line, code=code)
    if context_path:
        context += f" (at {context_path})"

    are_equal = (left == right)

    if bakery is not None:
        from bakery.assertions import student_tests, QUIET
        student_tests.tests += 1
        if None not in (line, code):
            student_tests.lines.append(line)
        if are_equal:
            if not QUIET:
                print(_MSG_SUCCESS.format(context=context))
            student_tests.successes += 1
        else:
            print(_MSG_FAILURE.format(context=context, x=repr(left), y=repr(right)))
            student_tests.failures += 1
    else:
        if are_equal:
            print(_MSG_SUCCESS.format(context=context))
        else:
            print(_MSG_FAILURE.format(context=context, x=repr(left), y=repr(right)))

    return are_equal


def _compare_page_contents(left, right, context_path: str, line, code) -> bool:
    """
    Recursively compare two page-content values, ignoring style-related fields.

    Rules:
    - Lists are compared element-by-element.
    - A ``str`` and a :class:`~drafter.components.Text` object are considered
      equal when the string matches ``Text.body`` (styles are ignored).
    - Two :class:`~drafter.components.PageContent` instances are compared by
      their declared dataclass fields; for any field named ``extra_settings``
      only non-``style_*`` keys are considered.
    - Simple primitives are compared directly.
    """
    # Import here to avoid circular imports at module load time.
    from drafter.components import PageContent, Text

    # --- list vs list -------------------------------------------------------
    if isinstance(left, list) and isinstance(right, list):
        if not _page_report(len(left), len(right),
                            context_path + ".length", line, code):
            return False
        result = True
        for i, (l, r) in enumerate(zip(left, right)):
            if not _compare_page_contents(l, r, f"{context_path}[{i}]", line, code):
                result = False
        return result

    # --- str vs Text (or vice-versa) ignoring styles ------------------------
    if isinstance(left, str) and isinstance(right, Text):
        return _page_report(left, right.body, context_path, line, code)
    if isinstance(left, Text) and isinstance(right, str):
        return _page_report(left.body, right, context_path, line, code)

    # --- simple primitives --------------------------------------------------
    if isinstance(left, SIMPLE_PRIMITIVE_TYPES) and isinstance(right, SIMPLE_PRIMITIVE_TYPES):
        return _page_report(left, right, context_path, line, code)

    # --- PageContent vs PageContent -----------------------------------------
    if isinstance(left, PageContent) and isinstance(right, PageContent):
        # Type must match
        if not _page_report(type(left).__name__, type(right).__name__,
                            context_path + ".<type>", line, code):
            return False
        if type(left) is not type(right):
            return False

        if is_dataclass(left):
            result = True
            for field in dataclass_fields(left):
                l_val = getattr(left, field.name)
                r_val = getattr(right, field.name)
                field_path = f"{context_path}.{field.name}"

                if field.name == 'extra_settings':
                    # Compare only non-style keys
                    l_filtered = _filter_non_style_settings(l_val)
                    r_filtered = _filter_non_style_settings(r_val)
                    if not _page_report(l_filtered, r_filtered, field_path, line, code):
                        result = False
                else:
                    if not _compare_page_contents(l_val, r_val, field_path, line, code):
                        result = False
            return result

        # Non-dataclass PageContent: fall through to direct comparison
        return _page_report(left, right, context_path, line, code)

    # --- fallback: direct comparison ----------------------------------------
    return _page_report(left, right, context_path, line, code)


def assert_page(left, right) -> bool:
    """
    Assert that two :class:`~drafter.page.Page` objects are structurally equal,
    ignoring style-related differences.

    This function mirrors the behaviour of ``assert_equal`` from the Bakery
    testing library but is specialised for :class:`~drafter.page.Page` objects:

    - The ``state`` of both pages must be equal.
    - The ``content`` lists are compared recursively.
    - Style fields (``extra_settings`` keys starting with ``style_``) are
      ignored when comparing :class:`~drafter.components.PageContent` objects.
    - A plain string on one side may be compared to a
      :class:`~drafter.components.Text` object on the other side; only the
      text body is compared (styles are ignored).

    Messages are printed in the same format as the Bakery ``assert_equal``,
    including the source-code line and path into the ``Page`` structure where
    a mismatch was found.

    :param left:  The :class:`~drafter.page.Page` produced by the function
                  under test (the *actual* result).
    :param right: The expected :class:`~drafter.page.Page`.
    :returns: ``True`` if the pages are considered equal, ``False`` otherwise.
    """
    from drafter.page import Page

    line, code = _get_assert_page_line_code()

    # Validate types
    if bakery is not None:
        from bakery.assertions import assert_type
        assert_type(left, Page)
        assert_type(right, Page)
    else:
        if not isinstance(left, Page):
            print(_MSG_FAILURE.format(
                context=_MSG_LINE_CODE.format(line=line, code=code) if None not in (line, code) else "",
                x=repr(left), y=repr(Page)))
            return False
        if not isinstance(right, Page):
            print(_MSG_FAILURE.format(
                context=_MSG_LINE_CODE.format(line=line, code=code) if None not in (line, code) else "",
                x=repr(right), y=repr(Page)))
            return False

    result = True
    if not _page_report(left.state, right.state, "Page.state", line, code):
        result = False
    if not _compare_page_contents(left.content, right.content,
                                  "Page.content", line, code):
        result = False
    return result
