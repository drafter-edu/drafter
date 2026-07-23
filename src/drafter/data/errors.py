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

from dataclasses import dataclass, field
import traceback as _traceback_module
from typing import Any, Dict, Optional

from drafter.data.correlation import Correlation

# ---------------------------------------------------------------------------
# Categories and severities
# ---------------------------------------------------------------------------

CATEGORY_SYSTEM = "system"
CATEGORY_REQUEST = "request"
CATEGORY_PAYLOAD = "payload"
CATEGORY_BRIDGE = "bridge"
CATEGORY_CONFIG = "config"
CATEGORY_RUNTIME = "runtime"

CATEGORIES = (
    CATEGORY_SYSTEM,
    CATEGORY_REQUEST,
    CATEGORY_PAYLOAD,
    CATEGORY_BRIDGE,
    CATEGORY_CONFIG,
    CATEGORY_RUNTIME,
)

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"
SEVERITY_CRITICAL = "critical"

SEVERITIES = (
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_ERROR,
    SEVERITY_CRITICAL,
)

# ---------------------------------------------------------------------------
# Status codes
# ---------------------------------------------------------------------------

#: Successful response.
STATUS_OK = "ok"
#: The request itself was malformed (e.g. argument parsing failed).
STATUS_BAD_REQUEST = "bad_request"
#: No matching route was found.
STATUS_NOT_FOUND = "not_found"
#: A server-side failure (route execution, payload, bridge, system, etc.).
STATUS_ERROR = "error"

STATUSES = (
    STATUS_OK,
    STATUS_BAD_REQUEST,
    STATUS_NOT_FOUND,
    STATUS_ERROR,
)


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
    traceback: Optional[str] = None
    context: Correlation = field(default_factory=Correlation)
    status_code: Optional[str] = None
    recoverable: bool = True

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)
        if self.category not in CATEGORIES:
            raise ValueError(f"Unknown error category: {self.category!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"Unknown error severity: {self.severity!r}")
        if self.status_code is None:
            self.status_code = STATUS_ERROR
        elif self.status_code not in STATUSES:
            raise ValueError(f"Unknown status code: {self.status_code!r}")

    def to_json(self) -> Dict[str, Any]:
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
    message: Optional[str] = None,
    details: str = "",
    severity: str = SEVERITY_ERROR,
    context: Optional[Correlation] = None,
    status_code: Optional[str] = None,
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
        traceback_text: Optional[str] = "".join(
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
