"""Shared reporting machinery for Drafter's student-facing assertions.

Every assertion in `drafter.testing.asserts` funnels its result through
`report_assertion`, which:

- prints a student-friendly ``SUCCESS``/``FAILURE`` message to the
  console, including the line number of the test and a bulleted list of
  the specific differences found, and
- logs a `TestCaseEvent` (with a unified diff of the formatted values)
  so the debug panel's testing tab can display the result.

Default comparison behavior is controlled by `AssertionDefaults`, which
can be adjusted with `set_assertion_defaults` — for example, an
instructor can make style differences count by calling
``set_assertion_defaults(strict_styles=True)``.
"""

import difflib
from dataclasses import dataclass

from drafter.data.details.tests import TestCaseEvent
from drafter.history.formatting import format_page_content
from drafter.monitor.audit import log_record
from drafter.testing.assertions import ComparisonSettings
from drafter.testing.testing import get_line_code

MAX_REPORTED_DIFFERENCES = 10
"""Maximum number of individual differences printed for one failed assertion."""

MAX_VALUE_WIDTH = 300
"""Maximum number of characters shown when printing a value in a message."""


@dataclass
class AssertionDefaults:
    """Default flags applied to every assertion unless overridden per call.

    Attributes:
        precision: Number of decimal places used when comparing floats.
        exact_strings: Whether strings must match exactly; when False,
            strings are normalized (lowercased, whitespace-stripped)
            before comparison.
        strict_styles: Whether style/class attributes and CSS/JS metadata
            participate in comparisons; when False (the default) they
            are ignored, so cosmetic changes do not break tests.
        report_success: Whether passing assertions print a SUCCESS line.
    """

    precision: int = 4
    exact_strings: bool = False
    strict_styles: bool = False
    report_success: bool = True


_assertion_defaults = AssertionDefaults()


def get_assertion_defaults() -> AssertionDefaults:
    """Get the current global assertion default flags.

    Returns:
        AssertionDefaults: The mutable defaults object used by all
        assertions.
    """
    return _assertion_defaults


def set_assertion_defaults(
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    report_success: bool | None = None,
) -> AssertionDefaults:
    """Change the default flags used by all assertions.

    Only the provided (non-None) flags are changed. For example,
    ``set_assertion_defaults(strict_styles=True)`` makes every
    subsequent assertion treat style differences as failures, unless a
    specific call overrides it.

    Args:
        precision: Number of decimal places used when comparing floats.
        exact_strings: Whether strings must match exactly.
        strict_styles: Whether style differences count as failures.
        report_success: Whether passing assertions print a SUCCESS line.

    Returns:
        AssertionDefaults: The updated defaults.
    """
    if precision is not None:
        _assertion_defaults.precision = precision
    if exact_strings is not None:
        _assertion_defaults.exact_strings = exact_strings
    if strict_styles is not None:
        _assertion_defaults.strict_styles = strict_styles
    if report_success is not None:
        _assertion_defaults.report_success = report_success
    return _assertion_defaults


def resolve_settings(
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
) -> ComparisonSettings:
    """Build ComparisonSettings from per-call flags and global defaults.

    Args:
        precision: Per-call precision override, or None for the default.
        exact_strings: Per-call exact-strings override, or None for the
            default.
        strict_styles: Per-call strict-styles override, or None for the
            default.

    Returns:
        ComparisonSettings: The resolved settings for this assertion.
    """
    defaults = _assertion_defaults
    return ComparisonSettings(
        precision=defaults.precision if precision is None else precision,
        exact_strings=defaults.exact_strings
        if exact_strings is None
        else exact_strings,
        strict_styles=defaults.strict_styles
        if strict_styles is None
        else strict_styles,
    )


def shorten_value(value, width: int = MAX_VALUE_WIDTH) -> str:
    """Represent a value compactly for use inside a printed message.

    Args:
        value: The value to represent.
        width: Maximum number of characters before truncation.

    Returns:
        str: The (possibly truncated) repr of the value.
    """
    text = repr(value)
    if len(text) > width:
        return text[: width - 3] + "..."
    return text


def limit_details(details: list[str]) -> list[str]:
    """Cap the list of printed difference messages at a readable length.

    Args:
        details: All difference messages for a failed assertion.

    Returns:
        list[str]: At most MAX_REPORTED_DIFFERENCES messages, with a
        final "... and N more" line when some were omitted.
    """
    if len(details) <= MAX_REPORTED_DIFFERENCES:
        return details
    omitted = len(details) - MAX_REPORTED_DIFFERENCES
    return details[:MAX_REPORTED_DIFFERENCES] + [
        f"... and {omitted} more difference{'s' if omitted > 1 else ''}"
    ]


def report_assertion(
    kind: str,
    passed: bool,
    actual,
    expected,
    summary: str,
    details: list[str] | None = None,
    quiet: bool = False,
) -> bool:
    """Print and log the outcome of one assertion.

    On failure, prints a FAILURE message with the summary sentence and a
    bulleted list of specific differences. On success, prints a SUCCESS
    line (unless suppressed). Either way, a `TestCaseEvent` is emitted so
    the debug panel's testing tab can display the result along with a
    diff of the formatted values.

    Args:
        kind: The assertion's name (e.g., ``'assert_content'``).
        passed: Whether the assertion passed.
        actual: The actual value being checked.
        expected: The expected value (or search needle/pattern).
        summary: One student-friendly sentence explaining the failure.
        details: Individual difference messages to list under the summary.
        quiet: When True, suppress the printed SUCCESS message for this
            call (failures are always printed).

    Returns:
        bool: The `passed` value, so assertions can return it directly.
    """
    details = limit_details(details or [])
    line, code = get_line_code("assert_")
    if line is None or code is None:
        line, code = -1, "<unknown test code>"
    where = f" at line {line}" if line != -1 else ""

    message = ""
    if passed:
        if not quiet and _assertion_defaults.report_success:
            print(f"SUCCESS{where} ({kind})")
    else:
        lines = [f"FAILURE{where} ({kind}):", f"    {summary}"]
        lines.extend(f"      - {detail}" for detail in details)
        message = "\n".join([summary] + [f"- {detail}" for detail in details])
        print("\n".join(lines))

    # Emit the debug panel event. This must never break a student's test
    # run (for instance, when no Drafter server is active), so failures
    # to log are silently ignored.
    try:
        actual_formatted = format_page_content(actual, escape=False)
        expected_formatted = format_page_content(expected, escape=False)
        diff_html = ""
        if not passed:
            diff_html = "".join(
                difflib.unified_diff(
                    actual_formatted.splitlines(keepends=True),
                    expected_formatted.splitlines(keepends=True),
                    "Actually Returned",
                    "Test Expected",
                )
            )
        log_record(
            TestCaseEvent(
                line=line,
                caller=code,
                passed=passed,
                assertion_kind=kind,
                given=repr(actual),
                expected=repr(expected),
                given_formatted=actual_formatted,
                expected_formatted=expected_formatted,
                diff_html=diff_html,
                message=message,
            ),
            "testing.report_assertion",
        )
    except Exception:
        pass
    return passed
