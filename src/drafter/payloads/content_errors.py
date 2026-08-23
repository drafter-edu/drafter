"""Student-facing errors for problems inside page content.

Builds the `StudentFacingError` raised when the renderer meets a value it
cannot display, phrasing the location with the student-level path from
`drafter.data.paths` and tailoring the advice to the offending value's
type (a bare function suggests a `Link`, `None` suggests a missing
`return`, and so on).
"""

import types

from drafter.data.errors import StudentFacingError
from drafter.data.paths import PathItem, render_debug_path, render_student_path

SUPPORTED_CONTENT_SENTENCE = (
    "Pages can show text, numbers, booleans, images, and Drafter components."
)

_FUNCTION_TYPES = (
    types.FunctionType,
    types.MethodType,
    types.BuiltinFunctionType,
    types.BuiltinMethodType,
)


def short_repr(value, limit: int = 80) -> str:
    """A repr of `value` truncated to `limit` characters, never raising.

    Args:
        value: Any value, including ones with broken `__repr__`.
        limit: Maximum length of the result before truncation with `...`.

    Returns:
        str: The (possibly truncated) repr, or a type-based placeholder if
        repr itself fails.
    """
    try:
        text = repr(value)
    except Exception:
        return f"<unprintable {type(value).__name__} value>"
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def describe_content_value(value) -> str:
    """Name a value the way a novice would recognize it.

    Args:
        value: The unsupported content value.

    Returns:
        str: A phrase like "a dictionary (dict)" or "the function 'greet'".
    """
    if value is None:
        return "the value None"
    if isinstance(value, dict):
        return f"a dictionary ({short_repr(value)})"
    if isinstance(value, tuple):
        return f"a tuple ({short_repr(value)})"
    if isinstance(value, (set, frozenset)):
        return f"a set ({short_repr(value)})"
    if isinstance(value, _FUNCTION_TYPES):
        name = getattr(value, "__name__", "?")
        return f"the function '{name}' itself"
    if isinstance(value, type):
        return f"the class '{value.__name__}' itself"
    return f"a {type(value).__name__} value ({short_repr(value)})"


def advice_for_content_value(value) -> tuple[str, ...]:
    """Suggest fixes tailored to the type of an unsupported content value.

    Args:
        value: The unsupported content value.

    Returns:
        tuple[str, ...]: Friendly steps for the student to try.
    """
    if value is None:
        return (
            "A `None` here often means a function forgot to `return` something, "
            "or an `if` branch has no `return`.",
            "Check that every path through your route function returns content.",
        )
    if isinstance(value, dict):
        return (
            "Dictionaries cannot be shown directly. Convert one to text with "
            "`str(...)`, or show its data with a `Table`.",
            SUPPORTED_CONTENT_SENTENCE,
        )
    if isinstance(value, (tuple, set, frozenset)):
        kind_name = "tuple" if isinstance(value, tuple) else "set"
        return (
            f"Use a list `[...]` instead of a {kind_name} for page content.",
            SUPPORTED_CONTENT_SENTENCE,
        )
    if isinstance(value, _FUNCTION_TYPES):
        return (
            "A function by itself cannot be page content. If you meant to call "
            "it, add parentheses `(...)`.",
            "If you meant to link to another page, use `Link('text', "
            "the_function)` or a `Button`.",
        )
    if isinstance(value, type):
        return (
            "You used the class itself. Did you forget the parentheses "
            "`(...)` to create an instance?",
            SUPPORTED_CONTENT_SENTENCE,
        )
    return (
        "To display this value as text, wrap it in `str(...)`.",
        SUPPORTED_CONTENT_SENTENCE,
    )


def unsupported_content_error(value, path: list[PathItem]) -> StudentFacingError:
    """Build the error for a value the renderer cannot display.

    Args:
        value: The unsupported content value.
        path: The renderer's path from the page content root to the value.

    Returns:
        StudentFacingError: Carries a technical message with the full debug
        path and a friendly tier phrased with the student-level path.
    """
    student_path = render_student_path(path)
    debug_path = render_debug_path(path)
    location_sentence = (
        f" It is located at: {student_path}."
        if student_path
        else " It is at the top of your page content."
    )
    technical = (
        f"Unsupported page content type {type(value).__name__} "
        f"(value: {short_repr(value)})"
    )
    if debug_path:
        technical += f"\nAt {debug_path}"
    return StudentFacingError(
        technical,
        title="Page Content Problem",
        friendly=(
            "Your page content includes a value that Drafter does not know "
            f"how to display: {describe_content_value(value)}." + location_sentence
        ),
        steps=advice_for_content_value(value),
    )
