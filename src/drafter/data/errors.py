"""Canonical error contract for Drafter.

This module defines the single normalized error envelope used across the
Python server lifecycle, the Python bridge runtime, and (via JSON) the
TypeScript bootstrap/debug UI.

Every failure should ultimately be describable as an `ErrorDetails`:

- `id`: stable, code-like identifier (example: `request.route_not_found`).
- `category`: one of `CATEGORIES`.
- `severity`: one of `SEVERITIES`.
- `message`: human-safe message.
- `details`: developer-focused details.
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

import traceback as _traceback_module
from dataclasses import dataclass, field
from typing import Any

from drafter.data.correlation import Correlation

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

    Attributes:
        id: Stable, code-like identifier (example: `request.route_not_found`).
        category: One of `CATEGORIES`.
        message: Human-safe message.
        severity: One of `SEVERITIES` (default `error`).
        details: Developer-focused details.
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
    traceback: str | None = None
    context: Correlation = field(default_factory=Correlation)
    status_code: str | None = None
    recoverable: bool = True

    def __post_init__(self) -> None:
        """Initialize the Exception base and validate category, severity, and status."""
        Exception.__init__(self, self.message)
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
            "traceback": self.traceback,
            "context": self.context.to_json(),
            "status_code": self.status_code,
            "recoverable": self.recoverable,
        }


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
        message: Human-safe message; defaults to `str(exception)`.
        details: Developer-focused details.
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
    return ErrorDetails(
        id=error_id,
        category=category,
        message=message if message is not None else str(exception),
        severity=severity,
        details=details,
        traceback=traceback_text,
        context=context if context is not None else Correlation(),
        status_code=status_code,
        recoverable=recoverable,
    )
