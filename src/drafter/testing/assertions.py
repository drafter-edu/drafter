"""
Comparison machinery for testing Drafter sites.

This module is the engine underneath the student-facing assertion
functions in `drafter.testing.asserts`. It provides:

- `compare_equal` and its helpers, which recursively compare values
  (including Drafter components, payloads, and dataclasses) and report
  a list of `Difference` objects
- `search_content` for finding a value anywhere within nested page content
- `collect_text` for gathering the visible text chunks of page content

Comparison behavior is controlled by `ComparisonSettings` flags such as
`precision`, `exact_strings`, and `strict_styles` (style differences are
ignored by default).
"""

import dataclasses
from dataclasses import dataclass

# Number encapsulates bool, int, float, complex, decimal.Decimal, etc.
from numbers import Number
from typing import Any

from drafter.components.page_content import Component
from drafter.components.text import Text
from drafter.data.paths import PathItem, render_path
from drafter.payloads.kinds.fragment import Fragment
from drafter.testing.normalize import (
    LIST_GENERATOR_TYPES,
    SET_GENERATOR_TYPES,
    make_type_name,
    normalize_string,
)


@dataclass
class ComparisonSettings:
    """Flags controlling how `compare_equal` matches values.

    Attributes:
        precision: Number of decimal places used when comparing floats.
        exact_strings: Whether strings must match exactly; when False,
            strings are normalized (via Bakery) before comparison.
        strict_styles: Whether style/class attributes of Drafter components
            participate in comparisons; when False they are ignored.
    """

    precision: int = 4
    exact_strings: bool = False
    strict_styles: bool = False


@dataclass
class Difference:
    """A single mismatch found while comparing two values.

    Attributes:
        path: The PathItems leading from the root values to the mismatch.
        message: Human-readable description of the mismatch.
        actual: The actual value at the mismatch site.
        expected: The expected value at the mismatch site.
    """

    path: list[PathItem]
    message: str
    actual: Any
    expected: Any


def ignore_styles(attributes: dict) -> dict:
    """Filter style-related entries out of a component attribute mapping.

    Removes the `style` key, any key starting with `style`, and the
    `class`/`classes` keys, so that comparisons ignore presentation.

    Args:
        attributes: Attribute mapping from a component.

    Returns:
        dict: A new mapping without style- and class-related entries.
    """
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
        actual = list(actual)  # type: ignore[call-overload]
    if isinstance(expected, LIST_GENERATOR_TYPES):
        expected = list(expected)  # type: ignore[call-overload]
    if isinstance(actual, SET_GENERATOR_TYPES):
        actual = set(actual)  # type: ignore[call-overload]
    if isinstance(expected, SET_GENERATOR_TYPES):
        expected = set(expected)  # type: ignore[call-overload]

    # Check for special Drafter types (components, pages/fragments).
    # Styles are ignored inside this comparison unless strict_styles is set.
    differences = compare_drafter_types(actual, expected, settings, path)
    if differences is not None:
        return differences

    # Check for dataclasses (typically student-defined State classes)
    differences = compare_dataclasses(actual, expected, settings, path)
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
    """Report a mismatch between values of unrelated types.

    Args:
        actual: The actual value.
        expected: The expected value.
        settings: The comparison settings (unused).
        path: The path to the current element being compared.

    Returns:
        list[Difference]: A single Difference describing the type mismatch.
    """
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
    """Compare two values with plain equality as the fallback comparison.

    Args:
        actual: The actual value.
        expected: The expected value.
        settings: The comparison settings (unused).
        path: The path to the current element being compared.

    Returns:
        list[Difference]: Empty if `actual == expected`, otherwise a single
        Difference reporting the mismatch.
    """
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
    """Compare two same-type numbers for exact equality.

    Used for non-float numbers (ints, bools, Decimals, etc.); floats go
    through `compare_floats` instead.

    Args:
        actual: The actual number.
        expected: The expected number.
        settings: The comparison settings (unused).
        path: The path to the current element being compared.

    Returns:
        list[Difference]: Empty if equal, otherwise a single Difference
        reporting the mismatch.
    """
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
    """Compare two floats within a precision-based tolerance.

    The values are considered equal when their absolute difference is
    below `10 ** -settings.precision`.

    Args:
        actual: The actual float.
        expected: The expected float.
        settings: The comparison settings; `precision` sets the tolerance.
        path: The path to the current element being compared.

    Returns:
        list[Difference]: Empty if within tolerance, otherwise a single
        Difference reporting the mismatch.
    """
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
    """Compare two strings (or bytes values).

    When `settings.exact_strings` is set, the values must be exactly
    equal; otherwise both sides are normalized with Bakery's
    `_normalize_string` before comparison.

    Args:
        actual: The actual string or bytes.
        expected: The expected string or bytes.
        settings: The comparison settings; `exact_strings` controls
            normalization.
        path: The path to the current element being compared.

    Returns:
        list[Difference]: Empty if the strings match, otherwise a single
        Difference reporting the mismatch.
    """
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
        if normalize_string(actual) == normalize_string(expected):
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
    """Build the message reporting a sequence length mismatch.

    Args:
        actual_length: Length of the actual sequence.
        expected_length: Length of the expected sequence.

    Returns:
        str: A "Too many items" or "Too few items" message.
    """
    if actual_length > expected_length:
        return f"Too many items ({actual_length} > {expected_length})"
    else:
        return f"Too few items ({actual_length} < {expected_length})"


def compare_sequences(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference]:
    """Compare two lists or tuples element by element.

    Reports a length mismatch (if any), then compares elements pairwise up
    to the shorter length, with each element recorded under an `index`
    path step.

    Args:
        actual: The actual sequence.
        expected: The expected sequence.
        settings: The comparison settings.
        path: The path to the current element being compared.

    Returns:
        list[Difference]: All differences found; empty if the sequences
        match.
    """
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
    for i, (a, e) in enumerate(zip(actual, expected, strict=False)):
        diff = compare_equal(a, e, settings, path + [PathItem("index", str(i))])
        if diff:
            differences.extend(diff)
    return differences


def compare_sets(actual, expected, settings, path: list[PathItem]) -> list[Difference]:
    """Compare two sets (or frozenset values) by mutual containment.

    Every element of `actual` must compare equal to some element of
    `expected`, and vice versa; each unmatched element produces an
    "Item ... not found" Difference under a `set` path step.

    Args:
        actual: The actual set.
        expected: The expected set.
        settings: The comparison settings.
        path: The path to the current element being compared.

    Returns:
        list[Difference]: All differences found; empty if the sets match.
    """
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
    """Check that an item compares equal to at least one collection element.

    Args:
        item: The value to look for.
        collection: The iterable to search through.
        settings: The comparison settings.
        path: The path to the current element being compared.

    Returns:
        list[Difference]: Empty if some element matches, otherwise a single
        "Item ... not found" Difference.
    """
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
    """Compare two dictionaries by their keys, then their values.

    First compares the key sets (returning only those differences if the
    keys disagree); when the keys match, compares each pair of values
    under a `key` path step.

    Args:
        actual: The actual mapping.
        expected: The expected mapping.
        settings: The comparison settings.
        path: The path to the current element being compared.

    Returns:
        list[Difference]: The key differences, or all value differences;
        empty if the mappings match.
    """
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


def render_difference(difference: Difference) -> str:
    """Format a Difference as a human-readable message.

    Args:
        difference: The Difference to render.

    Returns:
        str: The difference's message, prefixed with "In <path>: " when
        the difference has a non-empty path.
    """
    if not difference.path:
        return difference.message
    path = render_path(difference.path)
    return f"In {path}: {difference.message}"


def compare_fragments(
    actual: Fragment, expected: Fragment, settings, path: list[PathItem]
) -> list[Difference]:
    """Compare two payloads (Fragments or Pages) by state and content.

    The states are compared first, then the content lists. The `target`,
    `css`, and `js` fields are treated as presentation details and only
    participate in the comparison when `settings.strict_styles` is set.

    Args:
        actual: The actual Fragment/Page.
        expected: The expected Fragment/Page.
        settings: The comparison settings.
        path: The path to the current element being compared.

    Returns:
        list[Difference]: All differences found; empty if the payloads match.
    """
    payload_name = make_type_name(expected)
    if type(actual) is not type(expected):
        return [
            Difference(
                path,
                f"Expected a {make_type_name(expected)} but got a {make_type_name(actual)}",
                actual=actual,
                expected=expected,
            )
        ]
    differences = compare_equal(
        actual.state,
        expected.state,
        settings,
        path + [PathItem("attributes", payload_name), PathItem("key", "state")],
    )
    differences += compare_equal(
        list(actual.content),
        list(expected.content),
        settings,
        path + [PathItem("attributes", payload_name), PathItem("key", "content")],
    )
    if settings.strict_styles:
        for field_name in ("target", "css", "js"):
            differences += compare_equal(
                getattr(actual, field_name),
                getattr(expected, field_name),
                settings,
                path
                + [PathItem("attributes", payload_name), PathItem("key", field_name)],
            )
    return differences


def compare_dataclasses(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference] | None:
    """Compare two dataclass instances field by field.

    Only applies when both values are dataclass instances (Drafter
    components are handled earlier by `compare_drafter_types`). Returns
    None when the comparison is not applicable so that `compare_equal`
    can fall through to other strategies.

    Args:
        actual: The actual value.
        expected: The expected value.
        settings: The comparison settings.
        path: The path to the current element being compared.

    Returns:
        list[Difference] | None: The differences between the two
        instances, or None when either value is not a dataclass instance.
    """
    if not dataclasses.is_dataclass(actual) or not dataclasses.is_dataclass(expected):
        return None
    # Dataclass *types* (as opposed to instances) are not compared here
    if isinstance(actual, type) or isinstance(expected, type):
        return None
    if type(actual) is not type(expected):
        return [
            Difference(
                path,
                f"Expected type {make_type_name(expected)} but got type {make_type_name(actual)}",
                actual=actual,
                expected=expected,
            )
        ]
    type_name = make_type_name(expected)
    differences = []
    for field in dataclasses.fields(expected):
        if not field.compare:
            continue
        differences.extend(
            compare_equal(
                getattr(actual, field.name),
                getattr(expected, field.name),
                settings,
                path + [PathItem("attributes", type_name), PathItem("key", field.name)],
            )
        )
    return differences


def compare_drafter_types(
    actual, expected, settings, path: list[PathItem]
) -> list[Difference] | None:
    """
    Compare special Drafter types (components and page payloads).
    Returns None if the comparison is not applicable.
    Unless `settings.strict_styles` is set, style attributes and any
    additional CSS/JS metadata are ignored.

    Args:
        actual (Any): The actual Drafter type instance.
        expected (Any): The expected Drafter type instance.
        settings (ComparisonSettings): The comparison settings.
        path (list[PathItem]): The path to the current element being compared.

    Returns:
        list[Difference]: A list of differences found between the actual and expected Drafter type instances, or None if not applicable.
    """
    if isinstance(actual, Fragment) and isinstance(expected, Fragment):
        return compare_fragments(actual, expected, settings, path)

    do_comparison = False
    component_name = "Unknown"
    actual_attributes: dict[str, Any] = {}
    actual_positional: dict[str, Any] = {}
    expected_attributes: dict[str, Any] = {}
    expected_positional: dict[str, Any] = {}

    if isinstance(actual, Text) and isinstance(expected, (str, int, float, bool)):
        do_comparison = True
        component_name = "text"
        actual_attributes, actual_positional = actual.get_fields()
        # Text stringifies plain bodies, so compare against the text form
        expected_attributes = {
            "body": expected if isinstance(expected, str) else str(expected)
        }

    if isinstance(actual, (str, int, float, bool)) and isinstance(expected, Text):
        do_comparison = True
        component_name = "text"
        actual_attributes = {"body": actual if isinstance(actual, str) else str(actual)}
        expected_attributes, expected_positional = expected.get_fields()

    if isinstance(actual, Component) and isinstance(expected, Component):
        # Simple path first, are they just equal? (Not usable when styles
        # are strict: component __eq__ may ignore extra settings/styles.)
        if not settings.strict_styles and actual == expected:
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
        if not settings.strict_styles:
            actual_attributes = ignore_styles(actual_attributes)
            expected_attributes = ignore_styles(expected_attributes)
        result = compare_mappings(
            actual_attributes,
            expected_attributes,
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
    """Compare the positional-argument mappings of two components.

    Reports missing and unexpected extra keys first (returning only those
    differences if any exist); otherwise compares each shared value under
    a `key` path step.

    Args:
        actual: Mapping of the actual component's positional arguments.
        expected: Mapping of the expected component's positional arguments.
        settings: The comparison settings.
        path: The path to the current element being compared.

    Returns:
        list[Difference]: The key differences, or all value differences;
        empty if the mappings match.
    """
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


def collect_text(actual, path: list[PathItem]) -> list[tuple[list[PathItem], str]]:
    """Collect the visible text chunks of page content.

    Walks through strings, Fragments/Pages, components (following only
    their content arguments, not their attributes), and composite
    containers, gathering every piece of text a user would see on the
    page. Numbers and booleans encountered as content are converted to
    their string form.

    Args:
        actual: The content to walk (a Fragment/Page, component, string,
            or a container of these).
        path: The current path within the content.

    Returns:
        list[tuple[list[PathItem], str]]: One (path, text) pair per text
        chunk found, in page order.
    """
    if isinstance(actual, str):
        return [(path, actual)]
    if isinstance(actual, bool) or isinstance(actual, (int, float)):
        return [(path, str(actual))]
    if isinstance(actual, Fragment):
        return collect_text(actual.content, path)
    if isinstance(actual, Component):
        component_name = make_type_name(actual)
        chunks = []
        for argument in actual.ARGUMENTS:
            if not argument.is_content:
                continue
            value = getattr(actual, argument.name, argument.default_value)
            if value is None:
                continue
            child_path = path + [
                PathItem("attributes", component_name),
                PathItem("key", argument.name),
            ]
            if argument.kind == "var":
                chunks.extend(collect_text(list(value), child_path))
            else:
                chunks.extend(collect_text(value, child_path))
        return chunks
    if isinstance(actual, dict):
        chunks = []
        for key, value in actual.items():
            chunks.extend(collect_text(value, path + [PathItem("key", str(key))]))
        return chunks
    if isinstance(actual, (list, tuple)):
        chunks = []
        for index, item in enumerate(actual):
            chunks.extend(collect_text(item, path + [PathItem("index", str(index))]))
        return chunks
    if isinstance(actual, (set, frozenset)):
        chunks = []
        for item in actual:
            chunks.extend(collect_text(item, path + [PathItem("set_item", str(item))]))
        return chunks
    return []


def get_component_children(component: Component) -> list[Any]:
    """Collect the direct child content of a component.

    Follows the component's declared content arguments (the same fields
    its renderer uses for child content), flattening var-args arguments
    and skipping None values. Unlike `Component.get_children`, this does
    not require a rendering context.

    Args:
        component: The component whose children should be collected.

    Returns:
        list[Any]: The child content items, in declaration order.
    """
    children: list[Any] = []
    for argument in component.ARGUMENTS:
        if not argument.is_content:
            continue
        value = getattr(component, argument.name, argument.default_value)
        if value is None:
            continue
        if argument.kind == "var":
            children.extend(value)
        else:
            children.append(value)
    return children
