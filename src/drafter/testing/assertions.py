"""
Assertions and comparison machinery for testing Drafter sites.

Currently provides:

- `assert_state` for checking the state of a Page (or Fragment) against an
  expected value, delegating to Bakery's `assert_equal`
- `compare_equal` and its helpers, which recursively compare values
  (including Drafter components) and report a list of `Difference` objects
- `search_content` for finding a value anywhere within nested page content

The following are unimplemented placeholder stubs that currently do
nothing: `assert_page`, `assert_content`, and `assert_has`.

Comparison behavior is controlled by `ComparisonSettings` flags such as
`precision`, `exact_strings`, and `strict_styles` (style differences are
ignored by default).
"""

from dataclasses import dataclass
from typing import Any, Optional

from bakery.assertions import (
    SET_GENERATOR_TYPES,
    LIST_GENERATOR_TYPES,
    _normalize_string,
    make_type_name,
)
from drafter.components.text import Text
from drafter.payloads.kinds.fragment import Fragment
from drafter.components.page_content import Component
from drafter.testing.testing import assert_equal

# Number encapsulates bool, int, float, complex, decimal.Decimal, etc.
from numbers import Number


@dataclass
class ComparisonSettings:
    precision: int = 4
    exact_strings: bool = False
    strict_styles: bool = False


@dataclass
class PathItem:
    kind: str
    name: str


@dataclass
class Difference:
    path: list[PathItem]
    message: str
    actual: Any
    expected: Any


def ignore_styles(attributes: dict) -> dict:
    return {
        key: value
        for key, value in attributes.items()
        if key != "style"
        and not key.startswith("style")
        and key not in ("classes", "class")
    }


def compare_equal(
    actual, expected, settings: ComparisonSettings, path: list[PathItem]
) -> list[Difference]:
    """
    Recursively compare two objects for equality, considering content, styles, and children.

    Args:
        actual (Any): The actual content of the Page.
        expected (Any): The expected content to compare against.
        settings (ComparisonSettings): The comparison settings to use.
        path (list[PathItem]): The path to the current element being compared.

    Returns:
        list[Difference]: A list of differences found between the actual and expected objects.
    """
    # Convert generator types to concrete types for comparison
    if isinstance(actual, LIST_GENERATOR_TYPES):
        actual = list(actual)
    if isinstance(expected, LIST_GENERATOR_TYPES):
        expected = list(expected)
    if isinstance(actual, SET_GENERATOR_TYPES):
        actual = set(actual)
    if isinstance(expected, SET_GENERATOR_TYPES):
        expected = set(expected)

    # Check for special Drafter types if we're not being strict about styles
    if not settings.strict_styles:
        differences = compare_drafter_types(actual, expected, settings, path)
        if differences is not None:
            return differences

    # Check for primitive types
    if isinstance(actual, float) and isinstance(expected, float):
        return compare_floats(actual, expected, settings, path)
    elif (
        isinstance(actual, Number)
        and isinstance(expected, Number)
        and isinstance(actual, type(expected))
    ):
        return compare_numbers(actual, expected, settings, path)
    elif (isinstance(actual, str) and isinstance(expected, str)) or (
        isinstance(actual, bytes) and isinstance(expected, bytes)
    ):
        return compare_strings(actual, expected, settings, path)
    # Compare composite types
    elif isinstance(actual, list) and isinstance(expected, list):
        return compare_sequences(actual, expected, settings, path)
    elif isinstance(actual, tuple) and isinstance(expected, tuple):
        return compare_sequences(actual, expected, settings, path)
    elif isinstance(actual, dict) and isinstance(expected, dict):
        return compare_mappings(actual, expected, settings, path)
    elif isinstance(actual, set) and isinstance(expected, set):
        return compare_sets(actual, expected, settings, path)
    elif isinstance(actual, frozenset) and isinstance(expected, frozenset):
        return compare_sets(actual, expected, settings, path)
    # Check for type mismatch
    elif not isinstance(actual, type(expected)):
        return compare_unrelated_types(actual, expected, settings, path)
    # Fallback for other types
    else:
        return compare_anything(actual, expected, settings, path)


def compare_unrelated_types(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    return [
        Difference(
            path,
            f"Expected type {make_type_name(expected)} but got type {make_type_name(actual)}",
            actual=actual,
            expected=expected,
        )
    ]


def compare_anything(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    if actual == expected:
        return []
    else:
        return [
            Difference(
                path,
                f"Expected {expected!r} but got {actual!r}",
                actual=actual,
                expected=expected,
            )
        ]


def compare_numbers(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    if actual == expected:
        return []
    else:
        return [
            Difference(
                path,
                f"Expected {expected!r} but got {actual!r}",
                actual=actual,
                expected=expected,
            )
        ]


def compare_floats(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    error = 10 ** (-settings.precision)
    if abs(actual - expected) < error:
        return []
    else:
        return [
            Difference(
                path,
                f"Expected {expected!r} but got {actual!r}",
                actual=actual,
                expected=expected,
            )
        ]


def compare_strings(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    if settings.exact_strings:
        if actual == expected:
            return []
        else:
            return [
                Difference(
                    path,
                    f"Expected {expected!r} but got {actual!r}",
                    actual=actual,
                    expected=expected,
                )
            ]
    else:
        if _normalize_string(actual) == _normalize_string(expected):
            return []
        else:
            return [
                Difference(
                    path,
                    f"Expected {expected!r} but got {actual!r}",
                    actual=actual,
                    expected=expected,
                )
            ]


def write_different_lengths_message(actual_length: int, expected_length: int) -> str:
    if actual_length > expected_length:
        return f"Too many items ({actual_length} > {expected_length})"
    else:
        return f"Too few items ({actual_length} < {expected_length})"


def compare_sequences(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    differences = []
    if len(actual) != len(expected):
        differences.append(
            Difference(
                path,
                write_different_lengths_message(len(actual), len(expected)),
                actual=actual,
                expected=expected,
            )
        )
    for i, (a, e) in enumerate(zip(actual, expected)):
        diff = compare_equal(a, e, settings, path + [PathItem("index", str(i))])
        if diff:
            differences.extend(diff)
    return differences


def compare_sets(actual, expected, settings, path: list[PathItem]) -> list[Difference]:
    differences = []
    for a in actual:
        diff = compare_contains(a, expected, settings, path + [PathItem("set", str(a))])
        if diff:
            differences.extend(diff)
    for e in expected:
        diff = compare_contains(e, actual, settings, path + [PathItem("set", str(e))])
        if diff:
            differences.extend(diff)
    return differences


def compare_contains(
    item, collection, settings, path: list[PathItem]
) -> list[Difference]:
    for e in collection:
        diff = compare_equal(item, e, settings, path + [PathItem("item", str(e))])
        if not diff:
            return []
    return [
        Difference(
            path,
            f"Item {item!r} not found",
            actual=item,
            expected=collection,
        )
    ]


def compare_mappings(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    actual_keys = set(actual.keys())
    expected_keys = set(expected.keys())
    differences = compare_sets(
        actual_keys, expected_keys, settings, path + [PathItem("keys", "")]
    )
    if differences:
        return differences
    all_differences = []
    for k in actual_keys:
        diff = compare_equal(
            actual[k], expected[k], settings, path + [PathItem("key", str(k))]
        )
        if diff:
            all_differences.extend(diff)
    return all_differences


def render_path(path: list[PathItem]) -> str:
    message = []
    remaining_parts = path[:]
    while remaining_parts:
        path_item = remaining_parts.pop(0)
        if path_item.kind == "attributes":
            if remaining_parts:
                next_path_item = remaining_parts.pop(0)
                message.append(f"{path_item.name} {next_path_item.name}")
            else:
                message.append(f"{path_item.name}")
        elif path_item.kind == "positional":
            if remaining_parts:
                next_path_item = remaining_parts.pop(0)
                if next_path_item.kind == "keys":
                    message.append(f"{path_item.name}")
                else:
                    message.append(f"{path_item.name} {next_path_item.name}")
            else:
                message.append(f"{path_item.name}")
        elif path_item.kind == "children":
            message.append(f"{path_item.name} children'")
        elif path_item.kind == "key":
            message.append(f"'{path_item.name}'")
        elif path_item.kind == "item":
            message.append(f"'{path_item.name}'")
        elif path_item.kind == "set":
            message.append(f"'{path_item.name}'")
        elif path_item.kind == "index":
            message.append(f"index '{path_item.name}'")
        else:
            message.append(f"{path_item.kind} '{path_item.name}'")
    return " ".join(message)


def render_difference(difference: Difference) -> str:
    if not difference.path:
        return difference.message
    path = render_path(difference.path)
    return f"In {path}: {difference.message}"


def compare_drafter_types(
    actual, expected, settings, path: list[PathItem]
) -> Optional[list[Difference]]:
    """
    Compare special Drafter types when not enforcing strict styles.
    Returns None if the comparison is not applicable.
    This basically ignores the styles of the Drafter types, and any additional
    CSS/JS metadata.

    Args:
        actual (Any): The actual Drafter type instance.
        expected (Any): The expected Drafter type instance.
        settings (ComparisonSettings): The comparison settings.
        path (list[PathItem]): The path to the current element being compared.

    Returns:
        list[Difference]: A list of differences found between the actual and expected Drafter type instances, or None if not applicable.
    """
    # if isinstance(actual, Fragment) and isinstance(expected, Fragment):
    #    pass
    # Allowed to flatten content in some cases
    # if isinstance(actual, Component) and isinstance(expected, (list, tuple)):

    do_comparison = False
    component_name = "Unknown"
    actual_attributes, actual_positional = {}, {}
    expected_attributes, expected_positional = {}, {}

    if isinstance(actual, Text) and isinstance(expected, str):
        do_comparison = True
        component_name = "text"
        actual_attributes, actual_positional = actual.get_fields()
        expected_attributes = {"body": expected}

    if isinstance(actual, str) and isinstance(expected, Text):
        do_comparison = True
        component_name = "text"
        actual_attributes = {"body": actual}
        expected_attributes, expected_positional = expected.get_fields()

    if isinstance(actual, Component) and isinstance(expected, Component):
        # Simple path first, are they just equal?
        if actual == expected:
            return []

        # Check if the same type
        if not isinstance(actual, type(expected)):
            return [
                Difference(
                    path,
                    f"Expected type {make_type_name(expected)} but got type {make_type_name(actual)}",
                    actual=actual,
                    expected=expected,
                )
            ]
        component_name = make_type_name(expected)
        # Check all of the fields
        actual_attributes, actual_positional = actual.get_fields()
        expected_attributes, expected_positional = expected.get_fields()
        do_comparison = True

    if do_comparison:
        # print("Actual Positional:", actual_positional)
        # print("Expected Positional:", expected_positional)
        # print("Actual Attributes:", actual_attributes)
        # print("Expected Attributes:", expected_attributes)
        result = compare_mappings(
            ignore_styles(actual_attributes),
            ignore_styles(expected_attributes),
            settings,
            path + [PathItem("attributes", component_name)],
        )
        result += compare_positional(
            actual_positional,
            expected_positional,
            settings,
            path + [PathItem("positional", component_name)],
        )
        # Return result
        return result

    return None


def compare_positional(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    differences = []
    actual_keys = set(actual.keys())
    expected_keys = set(expected.keys())
    missing_keys = sorted(expected_keys - actual_keys)
    extra_keys = sorted(actual_keys - expected_keys)
    if missing_keys:
        differences.append(
            Difference(
                path + [PathItem("keys", "")],
                f"Expected values missing in {', '.join(map(str, missing_keys))}",
                actual=actual,
                expected=expected,
            )
        )
    if extra_keys:
        differences.append(
            Difference(
                path + [PathItem("keys", "")],
                f"Unexpected extra values found in {', '.join(map(str, extra_keys))}",
                actual=actual,
                expected=expected,
            )
        )
    if differences:
        return differences
    for k in actual_keys:
        diff = compare_equal(
            actual[k], expected[k], settings, path + [PathItem("key", str(k))]
        )
        if diff:
            differences.extend(diff)
    return differences


def search_content(
    actual, needle, settings, path: list[PathItem]
) -> list[list[PathItem]]:
    """
    Search through the `actual` value and look for anything equal to `needle`.

    Args:
        actual: The actual content to search through.
        needle: The value to search for within the actual content.
        settings: The settings to use for comparison.
        path: The current path within the content, used for tracking nested locations.

    Returns:
        list[list[PathItem]]: A list of paths, one per match, where each
        path is the list of PathItems leading to a matching value. Empty
        if no matches were found.
    """
    # Did we find it?
    differences = compare_equal(actual, needle, settings, path)
    if not differences:
        return [path]

    # Drafter specific content
    if isinstance(actual, Fragment):
        return search_content(actual.content, needle, settings, path)
    if isinstance(actual, Component):
        component_name = make_type_name(actual)
        actual_attributes, actual_positional = actual.get_fields()
        matches = []
        for key, value in actual_attributes.items():
            matches.extend(
                search_content(
                    value,
                    needle,
                    settings,
                    path
                    + [
                        PathItem("attributes", component_name),
                        PathItem("key", str(key)),
                    ],
                )
            )
        for key, value in actual_positional.items():
            matches.extend(
                search_content(
                    value,
                    needle,
                    settings,
                    path
                    + [
                        PathItem("positional", component_name),
                        PathItem("key", str(key)),
                    ],
                )
            )
        return matches

    # Composite types
    if isinstance(actual, (dict,)):
        matches = []
        for k, v in actual.items():
            matches.extend(
                search_content(v, needle, settings, path + [PathItem("key", str(k))])
            )
        return matches
    if isinstance(actual, (list, tuple)):
        matches = []
        for i, item in enumerate(actual):
            matches.extend(
                search_content(
                    item, needle, settings, path + [PathItem("index", str(i))]
                )
            )
        return matches

        return path
    if isinstance(actual, (set, frozenset)):
        matches = []
        for item in actual:
            matches.extend(
                search_content(
                    item, needle, settings, path + [PathItem("set_item", str(item))]
                )
            )
        return matches

    # Couldn't find it
    return []


def assert_page(
    actual, expected, precision=4, exact_strings=False, strict_styles=False
):
    """Unimplemented stub: does nothing. Intended to eventually assert that a Page matches expected content, ignoring style differences by default."""


def assert_content(
    actual, expected, precision=4, exact_strings=False, strict_styles=False
):
    """Unimplemented stub: does nothing."""


def assert_state(
    actual, expected, precision=4, exact_strings=False, strict_styles=False
):
    """
    Assert that the state of a Page matches the expected state.

    Args:
        actual: The actual state of the Page.
        expected: The expected state to compare against.
        precision: The number of decimal places to consider for numerical comparisons.
        exact_strings: Whether to require exact string matches.
        strict_styles: Whether to require exact style matches.
    """
    if isinstance(actual, Fragment):
        actual = actual.state
    if isinstance(expected, Fragment):
        expected = expected.state
    assert_equal(
        actual,
        expected,
        precision=precision,
        exact_strings=exact_strings,
        strict_styles=strict_styles,
    )


def assert_has(actual, needle, precision=4, exact_strings=False, strict_styles=False):
    """Unimplemented stub: does nothing."""
