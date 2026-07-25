"""Student-facing assertion functions for testing Drafter sites.

This is Drafter's testing toolkit. Instead of only checking
that an entire page is exactly equal to another (`assert_equal`), these
assertions let tests focus on the parts of a site that matter:

- `assert_equal` / `assert_page`: compare whole values or whole pages
- `assert_state`: compare only the state carried by a page
- `assert_content`: compare only the content (what is shown) of a page
- `assert_has` / `assert_in` (and `assert_not_has` / `assert_not_in`):
  flexibly check whether some content appears anywhere in a page
- `assert_has_regex` / `assert_in_regex`: check the page's visible text
  against a regular expression
- `assert_attribute`, `assert_style`, `assert_children`, `assert_text`:
  check the details of one specific component

Every assertion prints a student-friendly SUCCESS/FAILURE message,
returns True/False rather than raising, and logs a rich diff to the
debug panel's testing tab.

By default, comparisons are forgiving: strings are compared
case-insensitively with whitespace trimmed, floats are compared to four
decimal places, and style/CSS differences are ignored entirely. Each
assertion accepts `precision`, `exact_strings`, and `strict_styles`
flags to tighten (or further loosen) a single check, and
`drafter.testing.reporting.set_assertion_defaults` changes the defaults
for every check.
"""

import re
from typing import Any

from drafter.components.page_content import Component
from drafter.payloads.kinds.fragment import Fragment
from drafter.testing.assertions import (
    PathItem,
    collect_text,
    compare_equal,
    get_component_children,
    render_difference,
    render_path,
    search_content,
)
from drafter.testing.normalize import make_type_name, normalize_string
from drafter.testing.reporting import (
    report_assertion,
    resolve_settings,
    shorten_value,
)

MAX_TEXT_CHUNKS_SHOWN = 8
"""Maximum number of text chunks listed when describing a page's text."""


def _unwrap_state(value: Any) -> Any:
    """Extract the state from a Page/Fragment, or pass the value through.

    Args:
        value: A Page, Fragment, or a plain state value.

    Returns:
        The contained state (for payloads) or the value itself.
    """
    if isinstance(value, Fragment):
        return value.state
    return value


def _unwrap_content(value: Any) -> tuple[list | None, str | None]:
    """Extract a content list from a page, component, string, or list.

    Args:
        value: A Page/Fragment (its content is used), a single component
            or string (wrapped in a list), or a list/tuple of content.

    Returns:
        A tuple of (content list, error message). Exactly one of the two
        is None.
    """
    if isinstance(value, Fragment):
        return list(value.content), None
    if isinstance(value, (Component, str)):
        return [value], None
    if isinstance(value, (list, tuple)):
        return list(value), None
    return None, (
        f"a Page, a list of content, a component, or a string was expected, "
        f"but this was a {make_type_name(value)}: {shorten_value(value)}"
    )


def _describe_page_text(content: list) -> str:
    """Summarize the visible text of page content for a failure message.

    Args:
        content: The page's content list.

    Returns:
        A sentence listing the page's text chunks (or noting that the
        page had no text).
    """
    chunks = [text for _, text in collect_text(content, [])]
    if not chunks:
        return "The page did not contain any text at all."
    shown = ", ".join(repr(chunk) for chunk in chunks[:MAX_TEXT_CHUNKS_SHOWN])
    if len(chunks) > MAX_TEXT_CHUNKS_SHOWN:
        shown += f", ... ({len(chunks) - MAX_TEXT_CHUNKS_SHOWN} more)"
    return f"The page's text was: {shown}"


def assert_equal(
    actual: Any,
    expected: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that two values are equal, reporting each difference found.

    Works on any values, including whole Pages, components, lists,
    dictionaries, and dataclasses. Style differences are ignored unless
    `strict_styles` is set.

    Args:
        actual: The value your code actually produced.
        expected: The value the test expected.
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether strings must match exactly (case and
            whitespace included).
        strict_styles: Whether style differences count as failures.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the values matched, False otherwise.
    """
    settings = resolve_settings(precision, exact_strings, strict_styles)
    differences = compare_equal(actual, expected, settings, [])
    return report_assertion(
        "assert_equal",
        not differences,
        actual,
        expected,
        "The two values were different:",
        [render_difference(difference) for difference in differences],
        quiet=quiet,
    )


def assert_page(
    actual: Any,
    expected: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that a returned page matches an expected page.

    Compares both the state and the content of the two pages. Style
    differences (and any custom CSS/JS) are ignored unless
    `strict_styles` is set.

    Args:
        actual: The Page (or Fragment) your route actually returned.
        expected: The Page (or Fragment) the test expected.
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether strings must match exactly.
        strict_styles: Whether style differences count as failures.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the pages matched, False otherwise.
    """
    for label, value in (("first", actual), ("second", expected)):
        if not isinstance(value, Fragment):
            return report_assertion(
                "assert_page",
                False,
                actual,
                expected,
                f"The {label} value given to assert_page was not a Page:",
                [
                    f"It was a {make_type_name(value)}: {shorten_value(value)}",
                    "Make sure you call your route function and pass in the "
                    "Page it returns.",
                ],
                quiet=quiet,
            )
    settings = resolve_settings(precision, exact_strings, strict_styles)
    differences = compare_equal(actual, expected, settings, [])
    return report_assertion(
        "assert_page",
        not differences,
        actual,
        expected,
        "The page was different from what the test expected:",
        [render_difference(difference) for difference in differences],
        quiet=quiet,
    )


def assert_state(
    actual: Any,
    expected: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that a page's state matches the expected state.

    If either argument is a Page (or Fragment), its state is extracted
    automatically, so you can pass in either the whole page or just the
    state value.

    Args:
        actual: The Page your route returned, or a state value.
        expected: The expected state (or a Page holding it).
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether strings must match exactly.
        strict_styles: Whether style differences count as failures.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the states matched, False otherwise.
    """
    actual_state = _unwrap_state(actual)
    expected_state = _unwrap_state(expected)
    settings = resolve_settings(precision, exact_strings, strict_styles)
    differences = compare_equal(actual_state, expected_state, settings, [])
    return report_assertion(
        "assert_state",
        not differences,
        actual_state,
        expected_state,
        "The page's state was different from what the test expected:",
        [render_difference(difference) for difference in differences],
        quiet=quiet,
    )


def assert_content(
    actual: Any,
    expected: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that a page's content matches the expected content.

    Only the content (what is shown on the page) is compared; the state
    is ignored. Either argument can be a Page/Fragment, a list of
    content, or a single component or string.

    Args:
        actual: The Page your route returned (or its content).
        expected: The expected content (a Page, list, component, or
            string).
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether strings must match exactly.
        strict_styles: Whether style differences count as failures.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the content matched, False otherwise.
    """
    actual_content, actual_error = _unwrap_content(actual)
    expected_content, expected_error = _unwrap_content(expected)
    for label, error in (("first", actual_error), ("second", expected_error)):
        if error is not None:
            return report_assertion(
                "assert_content",
                False,
                actual,
                expected,
                f"The {label} value given to assert_content could not be "
                "understood as page content:",
                [error.capitalize()],
                quiet=quiet,
            )
    settings = resolve_settings(precision, exact_strings, strict_styles)
    differences = compare_equal(actual_content, expected_content, settings, [])
    return report_assertion(
        "assert_content",
        not differences,
        actual_content,
        expected_content,
        "The page's content was different from what the test expected:",
        [render_difference(difference) for difference in differences],
        quiet=quiet,
    )


def _find_in_content(
    kind: str,
    page: Any,
    needle: Any,
    negated: bool,
    precision: int | None,
    exact_strings: bool | None,
    strict_styles: bool | None,
    quiet: bool,
) -> bool:
    """Shared implementation for assert_has/assert_in and their negations.

    Args:
        kind: The assertion name to report.
        page: The page (or content) being searched.
        needle: The value to search for.
        negated: Whether the assertion passes when the needle is absent.
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether strings must match exactly.
        strict_styles: Whether style differences count as failures.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: Whether the assertion passed.
    """
    content, error = _unwrap_content(page)
    if error is not None:
        return report_assertion(
            kind,
            False,
            page,
            needle,
            f"The page given to {kind} could not be searched:",
            [error.capitalize()],
            quiet=quiet,
        )
    assert content is not None
    settings = resolve_settings(precision, exact_strings, strict_styles)
    matches = search_content(content, needle, settings, [])

    # For string needles, fall back to searching within the page's text,
    # so that partial text like "score:" can be found inside longer text.
    if not matches and isinstance(needle, str):
        for path, text in collect_text(content, []):
            if settings.exact_strings:
                found = needle in text
            else:
                found = normalize_string(needle) in normalize_string(text)
            if found:
                matches = [path]
                break

    if negated:
        details = []
        if matches and matches[0]:
            details.append(f"It was found in {render_path(matches[0])}")
        return report_assertion(
            kind,
            not matches,
            content,
            needle,
            f"The page contained {shorten_value(needle)}, "
            "but the test expected it to be absent:",
            details,
            quiet=quiet,
        )
    return report_assertion(
        kind,
        bool(matches),
        content,
        needle,
        f"Could not find {shorten_value(needle)} anywhere in the page:",
        [_describe_page_text(content)],
        quiet=quiet,
    )


def assert_has(
    page: Any,
    needle: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that a page contains some content, anywhere within it.

    The needle can be a string (matched against any text on the page,
    including partial matches within longer text) or a component (for
    example, ``assert_has(page, Button("Save", save_game))`` checks that
    the page has that button, no matter where it appears or how it is
    styled).

    Args:
        page: The Page (or content) to search through.
        needle: The content to look for.
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether text must match exactly (case and
            whitespace included) instead of loosely.
        strict_styles: Whether style differences prevent a match.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the content was found, False otherwise.
    """
    return _find_in_content(
        "assert_has",
        page,
        needle,
        False,
        precision,
        exact_strings,
        strict_styles,
        quiet,
    )


def assert_in(
    needle: Any,
    page: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that some content appears in a page (flipped assert_has).

    Identical to `assert_has`, but with the arguments in the same order
    as Python's ``needle in page`` expression.

    Args:
        needle: The content to look for.
        page: The Page (or content) to search through.
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether text must match exactly instead of loosely.
        strict_styles: Whether style differences prevent a match.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the content was found, False otherwise.
    """
    return _find_in_content(
        "assert_in",
        page,
        needle,
        False,
        precision,
        exact_strings,
        strict_styles,
        quiet,
    )


def assert_not_has(
    page: Any,
    needle: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that a page does NOT contain some content.

    The opposite of `assert_has`: the test passes when the needle cannot
    be found anywhere in the page.

    Args:
        page: The Page (or content) to search through.
        needle: The content that should be absent.
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether text must match exactly instead of loosely.
        strict_styles: Whether style differences prevent a match.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the content was absent, False if it was found.
    """
    return _find_in_content(
        "assert_not_has",
        page,
        needle,
        True,
        precision,
        exact_strings,
        strict_styles,
        quiet,
    )


def assert_not_in(
    needle: Any,
    page: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that some content does NOT appear in a page.

    Identical to `assert_not_has`, but with the arguments in the same
    order as Python's ``needle not in page`` expression.

    Args:
        needle: The content that should be absent.
        page: The Page (or content) to search through.
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether text must match exactly instead of loosely.
        strict_styles: Whether style differences prevent a match.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the content was absent, False if it was found.
    """
    return _find_in_content(
        "assert_not_in",
        page,
        needle,
        True,
        precision,
        exact_strings,
        strict_styles,
        quiet,
    )


def _find_regex_in_content(
    kind: str,
    page: Any,
    pattern: "str | re.Pattern",
    exact_strings: bool | None,
    quiet: bool,
) -> bool:
    """Shared implementation for the regex-based search assertions.

    Args:
        kind: The assertion name to report.
        page: The page (or content) being searched.
        pattern: The regular expression (a string or compiled pattern).
        exact_strings: When falsy (the default), string patterns are
            matched case-insensitively.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: Whether any of the page's text matched the pattern.
    """
    content, error = _unwrap_content(page)
    if error is not None:
        return report_assertion(
            kind,
            False,
            page,
            pattern,
            f"The page given to {kind} could not be searched:",
            [error.capitalize()],
            quiet=quiet,
        )
    assert content is not None
    settings = resolve_settings(None, exact_strings, None)
    if isinstance(pattern, str):
        flags = 0 if settings.exact_strings else re.IGNORECASE
        try:
            compiled = re.compile(pattern, flags)
        except re.error as regex_error:
            return report_assertion(
                kind,
                False,
                content,
                pattern,
                f"The pattern {pattern!r} is not a valid regular expression:",
                [str(regex_error)],
                quiet=quiet,
            )
    else:
        compiled = pattern
    matched = any(compiled.search(text) for _, text in collect_text(content, []))
    return report_assertion(
        kind,
        matched,
        content,
        compiled.pattern,
        f"No text in the page matched the pattern {compiled.pattern!r}:",
        [_describe_page_text(content)],
        quiet=quiet,
    )


def assert_has_regex(
    page: Any,
    pattern: "str | re.Pattern",
    exact_strings: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that some text on a page matches a regular expression.

    Every piece of visible text on the page is tested against the
    pattern with `re.search`. By default the match is case-insensitive;
    pass ``exact_strings=True`` to make it case-sensitive.

    Args:
        page: The Page (or content) to search through.
        pattern: The regular expression (a string or compiled pattern).
        exact_strings: Whether matching should be case-sensitive.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if any text matched the pattern, False otherwise.
    """
    return _find_regex_in_content(
        "assert_has_regex", page, pattern, exact_strings, quiet
    )


def assert_in_regex(
    pattern: "str | re.Pattern",
    page: Any,
    exact_strings: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check that a regular expression matches some text on a page.

    Identical to `assert_has_regex`, but with the pattern first.

    Args:
        pattern: The regular expression (a string or compiled pattern).
        page: The Page (or content) to search through.
        exact_strings: Whether matching should be case-sensitive.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if any text matched the pattern, False otherwise.
    """
    return _find_regex_in_content(
        "assert_in_regex", page, pattern, exact_strings, quiet
    )


def _require_component(kind: str, component: Any, quiet: bool) -> bool:
    """Report a friendly failure when a value is not a single component.

    Args:
        kind: The assertion name to report.
        component: The value that was supposed to be a component.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True when the value IS a component (no report is made);
        False after reporting the failure otherwise.
    """
    if isinstance(component, Component):
        return True
    details = [f"It was a {make_type_name(component)}: {shorten_value(component)}"]
    if isinstance(component, Fragment):
        details.append(
            "Pass in one component from the page's content instead, like "
            "page.content[0]."
        )
    report_assertion(
        kind,
        False,
        component,
        None,
        f"The first value given to {kind} was not a component "
        "(like a Button or TextBox):",
        details,
        quiet=quiet,
    )
    return False


def assert_attribute(
    component: Any,
    name: str,
    expected: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check the value of one attribute of a specific component.

    Looks up the attribute among the component's fields (like a
    Button's ``text`` or ``url``) and any extra settings passed to it
    (like ``id`` or ``disabled``). Route functions are compared by name,
    so ``assert_attribute(button, "url", save_game)`` works.

    Args:
        component: The component to inspect.
        name: The name of the attribute to check.
        expected: The expected value of that attribute.
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether strings must match exactly.
        strict_styles: Whether style differences count as failures.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the attribute existed and matched, False otherwise.
    """
    if not _require_component("assert_attribute", component, quiet):
        return False
    component_name = make_type_name(component)
    declared = [argument.name for argument in component.ARGUMENTS]
    available = declared + sorted(
        key for key in component.extra_settings if not key.startswith("style_")
    )

    found = False
    value: Any = None
    if name in declared:
        found = True
        value = getattr(component, name, None)
    else:
        for candidate in (name, name.replace("-", "_"), name.replace("_", "-")):
            if candidate in component.extra_settings:
                found = True
                value = component.extra_settings[candidate]
                break

    if not found:
        return report_assertion(
            "assert_attribute",
            False,
            component,
            expected,
            f"The {component_name} does not have an attribute named {name!r}:",
            ["The attributes available are: " + ", ".join(sorted(set(available)))],
            quiet=quiet,
        )

    if callable(value):
        value = getattr(value, "__name__", value)
    if callable(expected):
        expected = getattr(expected, "__name__", expected)

    settings = resolve_settings(precision, exact_strings, strict_styles)
    differences = compare_equal(
        value,
        expected,
        settings,
        [PathItem("attributes", component_name), PathItem("key", name)],
    )
    return report_assertion(
        "assert_attribute",
        not differences,
        value,
        expected,
        f"The {component_name}'s {name!r} attribute was different from "
        "what the test expected:",
        [render_difference(difference) for difference in differences],
        quiet=quiet,
    )


def _collect_styles(component: Component) -> dict[str, str]:
    """Gather all styles set directly on a component.

    Combines ``style_*`` settings (like ``style_color="red"``) with any
    properties in a raw ``style="..."`` attribute string.

    Args:
        component: The component to inspect.

    Returns:
        dict[str, str]: CSS property names (hyphenated) mapped to their
        values, as strings.
    """
    styles: dict[str, str] = {}
    raw = component.extra_settings.get("style", "")
    if isinstance(raw, str):
        for declaration in raw.split(";"):
            if ":" in declaration:
                prop, css_value = declaration.split(":", 1)
                styles[prop.strip().lower().replace("_", "-")] = css_value.strip()
    for key, css_value in component.extra_settings.items():
        if key.startswith("style_") and key != "style_":
            prop = key[len("style_") :].lower().replace("_", "-")
            styles[prop] = str(css_value)
    return styles


def assert_style(
    component: Any,
    style: str,
    expected: Any,
    exact_strings: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check the value of one CSS style set directly on a component.

    Unlike the other assertions (which ignore styles by default), this
    one exists specifically to test styling — for example,
    ``assert_style(button, "background_color", "red")``. Only styles set
    directly on the component (via ``style_*`` arguments, helpers like
    ``change_color``, or a ``style="..."`` attribute) can be seen;
    styles from CSS files or themes cannot.

    Args:
        component: The component to inspect.
        style: The CSS property name (either form works: ``"font-size"``
            or ``"font_size"``).
        expected: The expected value of that style (e.g., ``"red"``).
        exact_strings: Whether the value must match exactly (case and
            whitespace included) instead of loosely.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the style existed and matched, False otherwise.
    """
    if not _require_component("assert_style", component, quiet):
        return False
    component_name = make_type_name(component)
    styles = _collect_styles(component)
    if style.startswith("style_"):
        style = style[len("style_") :]
    prop = style.lower().replace("_", "-")
    if prop not in styles:
        if styles:
            hint = "The styles set on it are: " + ", ".join(sorted(styles))
        else:
            hint = "No styles are set directly on this component."
        return report_assertion(
            "assert_style",
            False,
            component,
            expected,
            f"The {component_name} does not have a {prop!r} style set on it:",
            [hint, "(Styles from CSS files or themes cannot be checked.)"],
            quiet=quiet,
        )
    actual_value = styles[prop]
    expected_value = str(expected)
    settings = resolve_settings(None, exact_strings, None)
    if settings.exact_strings:
        matched = actual_value == expected_value
    else:
        matched = normalize_string(actual_value) == normalize_string(expected_value)
    return report_assertion(
        "assert_style",
        matched,
        actual_value,
        expected_value,
        f"The {component_name}'s {prop!r} style was different from "
        "what the test expected:",
        [f"Expected {expected_value!r} but got {actual_value!r}"],
        quiet=quiet,
    )


def assert_children(
    component: Any,
    expected: Any,
    precision: int | None = None,
    exact_strings: bool | None = None,
    strict_styles: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check the child content of a specific component.

    Compares the component's children (the content nested inside it,
    like the items of a BulletedList or the contents of a Div) against
    the expected content. A single expected component or string is
    treated as a list of one child.

    Args:
        component: The component whose children should be checked.
        expected: The expected children (a list, or a single component
            or string).
        precision: Number of decimal places for float comparisons.
        exact_strings: Whether strings must match exactly.
        strict_styles: Whether style differences count as failures.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the children matched, False otherwise.
    """
    if not _require_component("assert_children", component, quiet):
        return False
    component_name = make_type_name(component)
    children = get_component_children(component)
    if isinstance(expected, (Component, str)):
        expected_children = [expected]
    elif isinstance(expected, (list, tuple)):
        expected_children = list(expected)
    else:
        expected_children = [expected]
    settings = resolve_settings(precision, exact_strings, strict_styles)
    differences = compare_equal(
        children,
        expected_children,
        settings,
        [PathItem("children", component_name)],
    )
    return report_assertion(
        "assert_children",
        not differences,
        children,
        expected_children,
        f"The {component_name}'s children were different from what the test expected:",
        [render_difference(difference) for difference in differences],
        quiet=quiet,
    )


def assert_text(
    target: Any,
    expected: str,
    exact_strings: bool | None = None,
    quiet: bool = False,
) -> bool:
    """Check the combined visible text of a page or component.

    All the text chunks of the target are collected (in page order) and
    joined with newlines, then compared to the expected text. This
    completely ignores structure and styling — only the words matter.
    By default the comparison is loose (case-insensitive, with
    whitespace trimmed); pass ``exact_strings=True`` for an exact match.

    Args:
        target: A Page, component, string, or list of content.
        expected: The full text the target should display.
        exact_strings: Whether the text must match exactly.
        quiet: Suppress the printed SUCCESS message when the test passes.

    Returns:
        bool: True if the text matched, False otherwise.
    """
    content, error = _unwrap_content(target)
    if error is not None:
        return report_assertion(
            "assert_text",
            False,
            target,
            expected,
            "The first value given to assert_text could not be "
            "understood as page content:",
            [error.capitalize()],
            quiet=quiet,
        )
    assert content is not None
    combined = "\n".join(text for _, text in collect_text(content, []))
    settings = resolve_settings(None, exact_strings, None)
    if settings.exact_strings:
        matched = combined == expected
    else:
        # Loose matching collapses ALL whitespace (including line breaks),
        # so students don't have to guess where text chunks split.
        collapsed_actual = " ".join(combined.lower().split())
        collapsed_expected = " ".join(str(expected).lower().split())
        matched = collapsed_actual == collapsed_expected
    return report_assertion(
        "assert_text",
        matched,
        combined,
        expected,
        "The text was different from what the test expected:",
        [f"Expected {shorten_value(expected)} but got {shorten_value(combined)}"],
        quiet=quiet,
    )
