"""Central student-friendly error explanations.

Every student-visible error in Drafter is described by an `ErrorDetails`
envelope (see `drafter.data.errors`) carrying two tiers of text: the
technically concise `message`/`details`/`traceback`, and the
student-friendly `friendly_title`/`friendly_message`/`friendly_steps`.
This module is the single place the friendly tier is computed, at
envelope-creation time, while the original exception object is still
available.

`explain` resolves the friendly text through a fixed precedence:

1. Text carried by the exception itself (`friendly_title` /
   `friendly_message` / `friendly_steps` attributes, e.g. from
   `StudentFacingError` or a re-raised `ErrorDetails`).
2. Structured parameter diagnostics (a `diagnostics` attribute of
   `RouteDiagnostic`-like values, e.g. from `ParameterBindingError`).
3. A curated table keyed by the exact error id (`ID_EXPLANATIONS`).
4. A table keyed by the exception type (`EXCEPTION_EXPLANATIONS`),
   matched against the exception's MRO so subclasses inherit entries.
5. A per-category entry (`CATEGORY_EXPLANATIONS`) plus generic fallbacks.

The title, the message, and the steps resolve independently, so (for
example) an exception that carries only a friendly message still gets a
type-derived title and steps. All tables are plain data: adding a new
explanation is a one-line table entry, not new control flow.

Step strings may mark code fragments with backticks (like `` `this` ``);
renderers turn those into inline-code styling.
"""

from collections.abc import Callable, Iterable
from typing import Any, NamedTuple

# ---------------------------------------------------------------------------
# Generic fallbacks
# ---------------------------------------------------------------------------

GENERIC_TITLE = "Something Went Wrong"
"""Friendly page title used when no more specific title applies."""

GENERIC_MESSAGE = (
    "Your program hit an error and stopped this request before it could finish."
)
"""Friendly message used when no more specific explanation applies."""

GENERIC_STEPS: tuple[str, ...] = (
    "Read the technical message above.",
    "If that is not clear, then read the traceback and locate the first relevant line.",
    "Hypothesize what you think the error means, then check your code to see if that is true.",
    "Fix that first error, then run again and see if any new message appears.",
    "If you are stuck, seek help on what the error ID and traceback mean.",
)
"""General debugging advice used when no more specific steps apply."""


class Explanation(NamedTuple):
    """The student-friendly tier for one failure."""

    title: str
    message: str
    steps: tuple[str, ...]


# ---------------------------------------------------------------------------
# Explanations keyed by error id (most specific, curated per failure point)
# ---------------------------------------------------------------------------

ID_EXPLANATIONS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "request.route_not_found": (
        "Page Not Found",
        "Drafter could not find the page route your app tried to open.",
        (
            "Check route names and links so they match exactly (including dashes and slashes).",
            "Confirm that the route is added before your app starts handling requests.",
            "Use the 'Return to Index Page' link below to get back to a known page.",
        ),
    ),
    "request.argument_parsing_failed": (
        # Title only: the message and steps come from the structured
        # parameter diagnostics carried by the exception (rule 2).
        "Problem With the Route's Arguments",
        "",
        (),
    ),
    "system.error_page_failed": (
        "Something Went Very Wrong",
        "Drafter hit a second problem while trying to show you the error page itself.",
        (
            "Reload the application to get back to a working page.",
            "Read the technical message for the original problem.",
            "If this keeps happening, submit a bug report so it can be fixed.",
        ),
    ),
}
"""Friendly (title, message, steps) for specific error ids.

These win over exception-type entries because the framework-assigned id
describes what the failure means to the student better than whatever
internal exception happened to be raised. Empty parts mean "no
contribution" and resolve through the remaining rules.
"""

# ---------------------------------------------------------------------------
# Explanations keyed by exception type
# ---------------------------------------------------------------------------

#: A friendly message may be a plain sentence or a formatter that inspects
#: the exception to mention the specific name/key involved.
_MessageSource = str | Callable[[BaseException], str]


def _name_error_message(exception: BaseException) -> str:
    name = getattr(exception, "name", None)
    if name:
        return (
            f"Your code used the name '{name}', but that name has not been "
            "created yet (or was misspelled)."
        )
    return "Your code used a name that has not been created yet (or was misspelled)."


def _attribute_error_message(exception: BaseException) -> str:
    name = getattr(exception, "name", None)
    if name:
        return (
            f"Your code asked a value for '.{name}', but that value does not "
            "have anything with that name."
        )
    return "Your code asked a value for an attribute or method that it does not have."


def _key_error_message(exception: BaseException) -> str:
    args = getattr(exception, "args", ())
    if args:
        return (
            f"Your code looked up the key {args[0]!r} in a dictionary, "
            "but that key is not there."
        )
    return "Your code looked up a dictionary key that is not there."


def _import_error_message(exception: BaseException) -> str:
    name = getattr(exception, "name", None)
    if name:
        return (
            f"Python could not find or load the module '{name}' that your code imports."
        )
    return "Python could not find or load a module that your code imports."


EXCEPTION_EXPLANATIONS: dict[type, tuple[str, _MessageSource, tuple[str, ...]]] = {
    IndentationError: (
        "Indentation Problem",
        "Python was confused by the indentation (the spaces at the start) of one of your lines.",
        (
            "Look at the line number shown and compare its indentation with the lines around it.",
            "Use consistent indentation (four spaces per level) and do not mix tabs with spaces.",
            "Make sure the lines after a colon (`:`) are indented one extra level.",
        ),
    ),
    SyntaxError: (
        "Python Couldn't Read Your Code",
        "Python could not understand part of your code, so it stopped before running it.",
        (
            "Go to the file and line number shown in the traceback.",
            "Check for missing colons, commas, quotes, or parentheses on that line.",
            "Run again after fixing one syntax problem at a time.",
        ),
    ),
    NameError: (
        "Unknown Name",
        _name_error_message,
        (
            "Look for a misspelled variable or function name.",
            "Make sure the variable is created before you use it.",
            "Check capitalization because Python names are case-sensitive.",
        ),
    ),
    TypeError: (
        "Type Mismatch",
        "Your code tried to use a value in a way that does not work for its "
        "type (for example, mixing text and numbers).",
        (
            "Check that each function call has the right number of arguments.",
            "Verify that values have the type your code expects (for example, text vs number).",
            "Print intermediate values to see what type they are before the failing line.",
        ),
    ),
    IndexError: (
        "List Position Out of Range",
        "Your code asked for a position in a list that does not exist.",
        (
            "Check that the list actually has an item at that position (positions start at 0).",
            "Print the list length right before the failing line.",
            "Add a guard condition so positions past the end are handled safely.",
        ),
    ),
    KeyError: (
        "Missing Dictionary Key",
        _key_error_message,
        (
            "Check that the key exists in the dictionary before using it (try the `in` operator).",
            "Print the dictionary keys right before the failing line.",
            "Watch out for capitalization and extra spaces in the key.",
        ),
    ),
    AttributeError: (
        "Missing Attribute",
        _attribute_error_message,
        (
            "Check the spelling of the attribute or method name.",
            "Print `type(value)` before the failing line to make sure the value is what you expect.",
            "If the value could be `None`, add a check before using it.",
        ),
    ),
    ZeroDivisionError: (
        "Division by Zero",
        "Your code tried to divide by zero, which is not allowed.",
        (
            "Find the division on the failing line and work out when the bottom value could be zero.",
            "Add an `if` check so the division only happens when the bottom value is not zero.",
            "Print the values used in the division right before the failing line.",
        ),
    ),
    ImportError: (
        "Module Not Found",
        _import_error_message,
        (
            "Check the module name in the `import` statement for typos.",
            "Make sure the library is installed or available to your site.",
            "If it is one of your own files, confirm the file name matches the import.",
        ),
    ),
    RecursionError: (
        "Endless Recursion",
        "A function kept calling itself over and over without stopping, so Python gave up.",
        (
            "Find the function that calls itself and make sure it has a base case that stops.",
            "Check that each recursive call moves closer to the base case.",
            "If you did not mean to use recursion, look for a function accidentally calling itself.",
        ),
    ),
    FileNotFoundError: (
        "File Not Found",
        "Your code tried to open a file that Python could not find.",
        (
            "Check the file name and path for typos.",
            "Make sure the file is in the same folder as your code (or use the right path).",
            "Print the file name your code is using right before it opens the file.",
        ),
    ),
    ValueError: (
        "Unusable Value",
        "One of the values in your code had the right type, but its content "
        "was not something Python could use there.",
        (
            "Read the error message to see which value was not acceptable.",
            "Check the values you pass in on the failing line.",
            "Print the value right before the failing line to see what it actually is.",
        ),
    ),
}
"""Friendly (title, message, steps) keyed by exception type.

Matched against the exception's MRO, most-derived class first, so a
subclass entry (e.g. `IndentationError`) wins over its base
(`SyntaxError`) regardless of dict order, and unlisted subclasses fall
back to their nearest listed base.
"""

# ---------------------------------------------------------------------------
# Explanations keyed by category (title and message; steps stay generic)
# ---------------------------------------------------------------------------

CATEGORY_EXPLANATIONS: dict[str, tuple[str, str]] = {
    "request": (
        "Problem Loading This Page",
        "Drafter had trouble loading a page (route) from your app.",
    ),
    "payload": (
        "Problem Displaying This Page",
        "Drafter could not turn your page result into something it can display.",
    ),
    "runtime": (
        "Error in Your Code",
        "Your Python code ran into an error while it was executing.",
    ),
    "config": (
        "Configuration Problem",
        "Drafter found a configuration setting that it could not use.",
    ),
    "bridge": (
        "Browser Sync Problem",
        "Drafter had trouble syncing your Python code with the browser.",
    ),
}
"""Broad, per-category friendly (title, message) used when nothing else matched."""


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def _carried_friendly_text(
    exception: BaseException | None,
) -> tuple[str, str, tuple[str, ...]]:
    """Read friendly text the exception itself carries, if any.

    Any exception exposing `friendly_title`/`friendly_message`/
    `friendly_steps` attributes participates (e.g. `StudentFacingError`,
    or a re-wrapped `ErrorDetails`); empty values mean "not provided".
    """
    if exception is None:
        return "", "", ()
    title = getattr(exception, "friendly_title", "")
    message = getattr(exception, "friendly_message", "")
    steps = getattr(exception, "friendly_steps", ())
    if not isinstance(title, str):
        title = ""
    if not isinstance(message, str):
        message = ""
    try:
        steps = tuple(str(step) for step in steps)
    except TypeError:
        steps = ()
    return title, message, steps


def diagnostics_to_friendly(
    diagnostics: Iterable[Any],
    route_name: str = "",
) -> tuple[str, tuple[str, ...]]:
    """Convert parameter-pipeline diagnostics into friendly text.

    Args:
        diagnostics: `RouteDiagnostic`-like values (need `message`, `hint`,
            and optionally `route_name` attributes).
        route_name: Route to mention in the summary; when empty, taken from
            the first diagnostic that names one.

    Returns:
        A (friendly_message, friendly_steps) pair; ("", ()) when there are
        no diagnostics.
    """
    steps: list[str] = []
    for diagnostic in diagnostics:
        message = str(getattr(diagnostic, "message", "") or "")
        hint = str(getattr(diagnostic, "hint", "") or "")
        combined = f"{message} {hint}".strip()
        if combined:
            steps.append(combined)
        if not route_name:
            route_name = str(getattr(diagnostic, "route_name", "") or "")
    if not steps:
        return "", ()
    if route_name:
        summary = (
            "Drafter could not match the information sent by the page to the "
            f"parameters of your '{route_name}' function."
        )
    else:
        summary = (
            "Drafter could not match the information sent by the page to the "
            "parameters of your route function."
        )
    return summary, tuple(steps)


def _diagnostics_friendly_text(
    exception: BaseException | None,
) -> tuple[str, tuple[str, ...]]:
    """Friendly text from an exception's structured diagnostics, if any."""
    if exception is None:
        return "", ()
    diagnostics = getattr(exception, "diagnostics", None)
    if not diagnostics:
        return "", ()
    try:
        return diagnostics_to_friendly(diagnostics)
    except Exception:
        # Explanation is best-effort decoration; never let it mask the error.
        return "", ()


def _exception_type_explanation(
    exception: BaseException | None,
) -> tuple[str, str, tuple[str, ...]]:
    """Friendly text from the exception-type table, walking the MRO."""
    if exception is None:
        return "", "", ()
    for klass in type(exception).__mro__:
        entry = EXCEPTION_EXPLANATIONS.get(klass)
        if entry is None:
            continue
        title, message_source, steps = entry
        if callable(message_source):
            try:
                message = message_source(exception)
            except Exception:
                message = ""
        else:
            message = message_source
        return title, message, steps
    return "", "", ()


def explain(
    exception: BaseException | None,
    error_id: str,
    category: str,
) -> Explanation:
    """Produce student-friendly text for a failure.

    Args:
        exception: The originating exception, when there is one; classifying
            by the real exception type is what keeps explanations accurate.
        error_id: Stable envelope id (e.g. `request.route_execution_failed`).
        category: Envelope category (one of `drafter.data.errors.CATEGORIES`).

    Returns:
        An `Explanation` (title, message, steps). Every part always
        resolves (falling back to `GENERIC_TITLE`/`GENERIC_MESSAGE`/
        `GENERIC_STEPS`), and each part resolves independently through the
        precedence described in the module docstring.
    """
    carried_title, carried_message, carried_steps = _carried_friendly_text(exception)
    diagnostic_message, diagnostic_steps = _diagnostics_friendly_text(exception)
    id_title, id_message, id_steps = ID_EXPLANATIONS.get(error_id, ("", "", ()))
    type_title, type_message, type_steps = _exception_type_explanation(exception)
    category_title, category_message = CATEGORY_EXPLANATIONS.get(category, ("", ""))

    title = carried_title or id_title or type_title or category_title or GENERIC_TITLE
    message = (
        carried_message
        or diagnostic_message
        or id_message
        or type_message
        or category_message
        or GENERIC_MESSAGE
    )
    steps = carried_steps or diagnostic_steps or id_steps or type_steps or GENERIC_STEPS
    return Explanation(title, message, tuple(steps))
