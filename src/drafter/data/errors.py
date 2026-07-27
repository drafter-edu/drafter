"""Canonical error contract for Drafter.

This module defines the single normalized error envelope used across the
Python server lifecycle, the Python bridge runtime, and (via JSON) the
TypeScript bootstrap/debug UI.

Every failure should ultimately be describable as an `ErrorDetails`:

- `id`: stable, code-like identifier (example: `request.route_not_found`).
- `category`: one of `CATEGORIES`.
- `severity`: one of `SEVERITIES`.
- `message`: technically concise, accurate message.
- `details`: developer-focused free-text details.
- `data`: structured, JSON-safe details (nested dicts/lists), for renderers
  that can display them richly. Well-known keys: `route_call` (the generated
  route call string, e.g. `guess(state, 5)`), `route_call_exact` (whether
  that call string is the fully-bound call or a best-effort approximation),
  `request` (the structured request description).
- `friendly_title`: short page-title-style label for the failure.
- `friendly_message`: plain-language explanation for novice programmers.
- `friendly_steps`: concrete "what to try next" suggestions for students.
- `traceback`: optional traceback/stack text.
- `context`: correlation info (route, request_id, response_id, dom_id, phase).
- `status_code`: symbolic, HTTP-name-style status string (one of
  `STATUSES`); the precise failure is identified by `id`/`category`.
- `recoverable`: whether the application can continue after this error.

Status codes are a small, fixed set of symbolic strings with coarse
HTTP-like meaning (see `STATUSES`):

- `ok`: Successful response.
- `bad_request`: The request itself was malformed (e.g. argument parsing
  failed).
- `not_found`: No matching route was found.
- `error`: A server-side failure (route execution, payload handling,
  bridge, system, config, or runtime error).

The fine-grained distinction between failures lives in the envelope `id`
(for example `payload.rendering_failed`) and `category`; the status is
only a coarse outcome bucket used for responses and telemetry display.
"""

import dataclasses
import traceback as _traceback_module
from dataclasses import dataclass, field
from typing import Any

from drafter.data.correlation import Correlation

#: Maximum nesting depth kept when sanitizing structured error data.
_MAX_DATA_DEPTH = 8


def json_safe(value: Any, _depth: int = 0) -> Any:
    """Convert an arbitrary value into a JSON-safe structure.

    Scalars pass through; dicts/lists/tuples are converted recursively
    (dict keys become strings); objects offering a `to_json()` method are
    converted through it; dataclass instances become field dictionaries;
    anything else (or anything nested too deeply) becomes its `repr`
    string, so the result is always serializable and never raises.

    Args:
        value: The value to sanitize.
        _depth: Internal recursion depth counter.

    Returns:
        A structure containing only None, bool, int, float, str, list,
        and dict values.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if _depth >= _MAX_DATA_DEPTH:
        return repr(value)
    try:
        if isinstance(value, dict):
            return {
                str(key): json_safe(item, _depth + 1) for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [json_safe(item, _depth + 1) for item in value]
        to_json = getattr(value, "to_json", None)
        if callable(to_json):
            return json_safe(to_json(), _depth + 1)
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            # Shallow field walk (not dataclasses.asdict) so one bad or
            # deepcopy-hostile field cannot take down the whole conversion.
            return {
                data_field.name: json_safe(getattr(value, data_field.name), _depth + 1)
                for data_field in dataclasses.fields(value)
            }
        return repr(value)
    except Exception:
        # Sanitizing is best-effort decoration; never let it mask the error.
        try:
            return repr(value)
        except Exception:
            return "<unrepresentable value>"


# ---------------------------------------------------------------------------
# Categories and severities
# ---------------------------------------------------------------------------

CATEGORY_SYSTEM = "system"
"""Internal system failure."""
CATEGORY_REQUEST = "request"
"""Request handling failure (routing, argument parsing)."""
CATEGORY_PAYLOAD = "payload"
"""Payload rendering or handling failure."""
CATEGORY_BRIDGE = "bridge"
"""Python/JavaScript bridge failure."""
CATEGORY_CONFIG = "config"
"""Configuration failure."""
CATEGORY_RUNTIME = "runtime"
"""Runtime failure while executing user code."""

CATEGORIES = (
    CATEGORY_SYSTEM,
    CATEGORY_REQUEST,
    CATEGORY_PAYLOAD,
    CATEGORY_BRIDGE,
    CATEGORY_CONFIG,
    CATEGORY_RUNTIME,
)
"""All valid error categories."""

SEVERITY_INFO = "info"
"""Informational event, not a failure."""
SEVERITY_WARNING = "warning"
"""Recoverable problem worth surfacing."""
SEVERITY_ERROR = "error"
"""Failure of the current operation."""
SEVERITY_CRITICAL = "critical"
"""Failure the application cannot recover from."""

SEVERITIES = (
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_ERROR,
    SEVERITY_CRITICAL,
)
"""All valid error severities."""

# ---------------------------------------------------------------------------
# Status codes
# ---------------------------------------------------------------------------

STATUS_OK = "ok"
"""Successful response."""
STATUS_BAD_REQUEST = "bad_request"
"""The request itself was malformed (e.g. argument parsing failed)."""
STATUS_NOT_FOUND = "not_found"
"""No matching route was found."""
STATUS_ERROR = "error"
"""A server-side failure (route execution, payload, bridge, system, etc.)."""

STATUSES = (
    STATUS_OK,
    STATUS_BAD_REQUEST,
    STATUS_NOT_FOUND,
    STATUS_ERROR,
)
"""All valid symbolic status codes."""


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------
@dataclass
class ErrorDetails(Exception):
    """A container for details about an error, warning, or other negative event.

    The envelope carries two tiers of description: `message` (with `details`
    and `traceback`) is the technically concise, accurate tier, while
    `friendly_message` and `friendly_steps` are the student-friendly tier,
    normally filled in by `drafter.data.error_explainer.explain`. Renderers
    display both tiers; empty friendly fields mean "not provided" and
    renderers fall back to generic wording.

    Attributes:
        id: Stable, code-like identifier (example: `request.route_not_found`).
        category: One of `CATEGORIES`.
        message: Technically concise, accurate message.
        severity: One of `SEVERITIES` (default `error`).
        details: Developer-focused free-text details.
        data: Structured, JSON-safe details (sanitized through `json_safe`
            on construction). Well-known keys: `route_call`,
            `route_call_exact`, `request` (see the module docstring).
        friendly_title: Short page-title-style label for the failure
            (empty when not provided).
        friendly_message: Plain-language explanation for novice programmers
            (empty when not provided).
        friendly_steps: Concrete "what to try next" suggestions for students
            (empty when not provided).
        traceback: Optional traceback/stack text.
        context: Correlation context for the error.
        status_code: Symbolic status string (one of `STATUSES`);
            defaults to `STATUS_ERROR`.
        recoverable: Whether the application can continue after this error.
    """

    id: str
    category: str
    message: str
    severity: str = SEVERITY_ERROR
    details: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    friendly_title: str = ""
    friendly_message: str = ""
    friendly_steps: tuple[str, ...] = ()
    traceback: str | None = None
    context: Correlation = field(default_factory=Correlation)
    status_code: str | None = None
    recoverable: bool = True

    def __post_init__(self) -> None:
        """Initialize the Exception base and validate category, severity, and status."""
        Exception.__init__(self, self.message)
        # Accept any iterable of steps but store an immutable tuple.
        self.friendly_steps = tuple(self.friendly_steps)
        # Enforce the JSON-safety invariant once, at construction, so every
        # consumer (renderers, telemetry, the wire format) can rely on it.
        self.data = json_safe(dict(self.data))
        if self.category not in CATEGORIES:
            raise ValueError(f"Unknown error category: {self.category!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"Unknown error severity: {self.severity!r}")
        if self.status_code is None:
            self.status_code = STATUS_ERROR
        elif self.status_code not in STATUSES:
            raise ValueError(f"Unknown status code: {self.status_code!r}")

    def to_json(self) -> dict[str, Any]:
        """Converts the ErrorDetails instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the envelope, with the correlation
            context serialized via its own `to_json`.
        """
        return {
            "id": self.id,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "data": self.data,
            "friendly_title": self.friendly_title,
            "friendly_message": self.friendly_message,
            "friendly_steps": list(self.friendly_steps),
            "traceback": self.traceback,
            "context": self.context.to_json(),
            "status_code": self.status_code,
            "recoverable": self.recoverable,
        }


# ---------------------------------------------------------------------------
# Student-facing exceptions
# ---------------------------------------------------------------------------


class StudentFacingError(ValueError):
    """A `ValueError` that carries its own student-friendly explanation.

    Drafter code that raises errors students commonly trigger (bad component
    arguments, invalid names, and so on) can use this class to supply the
    friendly tier right at the raise site. `str(exception)` stays the
    technically concise message; the friendly text rides along on the
    `friendly_message`/`friendly_steps` attributes, which the central error
    explainer (`drafter.data.error_explainer.explain`) picks up with the
    highest precedence when the exception is wrapped into an envelope.

    Args:
        message: Technically concise, accurate message (becomes `str(self)`).
        friendly: Plain-language explanation for novice programmers.
        steps: Concrete "what to try next" suggestions.
        title: Short page-title-style label for the failure.
    """

    def __init__(
        self,
        message: str,
        *,
        friendly: str = "",
        steps: tuple[str, ...] | list[str] = (),
        title: str = "",
    ):
        super().__init__(message)
        self.friendly_title = title
        self.friendly_message = friendly
        self.friendly_steps = tuple(steps)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def envelope_from_exception(
    exception: BaseException,
    error_id: str,
    category: str,
    *,
    message: str | None = None,
    details: str = "",
    data: dict[str, Any] | None = None,
    friendly_title: str | None = None,
    friendly_message: str | None = None,
    friendly_steps: tuple[str, ...] | None = None,
    severity: str = SEVERITY_ERROR,
    context: Correlation | None = None,
    status_code: str | None = None,
    recoverable: bool = True,
) -> ErrorDetails:
    """Build a canonical envelope from a raised exception.

    Args:
        exception: The exception being normalized.
        error_id: Stable, code-like identifier for this failure.
        category: One of `CATEGORIES`.
        message: Technically concise message; defaults to `str(exception)`.
        details: Developer-focused free-text details.
        data: Structured, JSON-safe details (sanitized on construction).
        friendly_title: Student-friendly title; when None, one is derived
            from the exception via the central error explainer.
        friendly_message: Student-friendly explanation; when None, one is
            derived from the exception via the central error explainer.
        friendly_steps: Student-friendly fix suggestions; when None, they are
            derived from the exception via the central error explainer.
        severity: One of `SEVERITIES`.
        context: Correlation context.
        status_code: Symbolic status string; defaults to `STATUS_ERROR`.
        recoverable: Whether the application can continue after this error.

    Returns:
        An `ErrorDetails` envelope populated from the exception, with the
        formatted traceback attached when available. If traceback formatting
        itself fails, the traceback is silently omitted (set to None) rather
        than masking the original error.
    """
    try:
        traceback_text: str | None = "".join(
            _traceback_module.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )
    except Exception:
        # Defensive fallback: traceback formatting can itself fail (e.g., on
        # exotic exception objects); omit the traceback rather than let a
        # formatting error mask the original exception.
        traceback_text = None
    if friendly_title is None or friendly_message is None or friendly_steps is None:
        # Imported lazily so this leaf module stays import-cycle-free even
        # as explainer rules grow new dependencies.
        from drafter.data.error_explainer import explain

        derived = explain(exception, error_id, category)
        if friendly_title is None:
            friendly_title = derived.title
        if friendly_message is None:
            friendly_message = derived.message
        if friendly_steps is None:
            friendly_steps = derived.steps
    return ErrorDetails(
        id=error_id,
        category=category,
        message=message if message is not None else str(exception),
        severity=severity,
        details=details,
        data=data if data is not None else {},
        friendly_title=friendly_title,
        friendly_message=friendly_message,
        friendly_steps=tuple(friendly_steps),
        traceback=traceback_text,
        context=context if context is not None else Correlation(),
        status_code=status_code,
        recoverable=recoverable,
    )
