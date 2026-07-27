"""Small comparison helpers used by Drafter's testing framework.

These were originally vendored from the Bakery testing library so that
Drafter's assertions work identically whether or not Bakery is
installed. They cover type-name formatting, loose string
normalization, and the generator types that should be converted to
concrete lists/sets before comparison.
"""

LIST_GENERATOR_TYPES: tuple[type, ...] = (
    map,
    filter,
    range,
    type(reversed([])),
    zip,
    enumerate,
)
"""Lazy sequence types that are converted to lists before comparison."""

SET_GENERATOR_TYPES: tuple[type, ...] = (
    type({}.keys()),
    type({}.values()),
    type({}.items()),
)
"""Dictionary view types that are converted to sets before comparison."""


def make_type_name(value) -> str:
    """Get a human-friendly name for the type of a value.

    Args:
        value: Any value.

    Returns:
        The name of the value's type (e.g., ``'int'`` or ``'Button'``).
    """
    try:
        return type(value).__name__
    except Exception:
        return str(type(value))[8:-2]


def normalize_string(text: str) -> str:
    """Normalize a string for loose comparison.

    Lowercases the text, strips leading/trailing whitespace from each
    line, and removes blank lines. This matches Bakery's behavior for
    non-exact string comparisons.

    Args:
        text: The string to normalize.

    Returns:
        The normalized string.
    """
    text = text.lower()
    lines = text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(lines)
