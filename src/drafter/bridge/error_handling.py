"""Shared error-handling helpers for bridge-side runtime failures.

These helpers centralize exception normalization and telemetry reporting so
bridge modules can avoid ad hoc ``print`` + ``raise`` patterns.
"""

from typing import Any, Optional

from drafter.monitor.audit import log_error
from drafter.monitor.events.errors import DrafterError


def normalize_bridge_exception(error: Any) -> Exception:
    """Normalize unknown thrown values into an Exception instance."""
    if isinstance(error, Exception):
        return error
    if isinstance(error, BaseException):
        return RuntimeError(str(error))
    return RuntimeError(str(error))


def report_bridge_error(
    event_type: str,
    message: str,
    source: str,
    details: str,
    *,
    exception: Optional[Any] = None,
    request_id: Optional[int] = None,
    response_id: Optional[int] = None,
    dom_id: Optional[str] = None,
    route: Optional[str] = None,
) -> DrafterError:
    """Log a bridge error and return a DrafterError payload.

    Falls back to an in-memory DrafterError if telemetry logging itself fails.
    """
    normalized_exception = (
        normalize_bridge_exception(exception) if exception is not None else None
    )
    try:
        return log_error(
            event_type,
            message,
            source,
            details,
            exception=normalized_exception,
            request_id=request_id,
            response_id=response_id,
            dom_id=dom_id,
            route=route,
        )
    except Exception as logging_error:
        # Last-resort fallback: keep an actionable local error object even if
        # event bus/telemetry plumbing is unavailable.
        fallback_details = (
            f"{details}\nTelemetry logging failure: {repr(logging_error)}"
        )
        return DrafterError(
            message=message,
            where=source,
            details=fallback_details,
            traceback=None,
        )


def raise_bridge_system_error(
    event_type: str,
    message: str,
    source: str,
    details: str,
    *,
    exception: Optional[Any] = None,
    request_id: Optional[int] = None,
    response_id: Optional[int] = None,
    dom_id: Optional[str] = None,
    route: Optional[str] = None,
) -> None:
    """Log and raise a normalized RuntimeError for bridge system failures."""
    normalized_exception = (
        normalize_bridge_exception(exception) if exception is not None else None
    )
    drafter_error = report_bridge_error(
        event_type,
        message,
        source,
        details,
        exception=normalized_exception,
        request_id=request_id,
        response_id=response_id,
        dom_id=dom_id,
        route=route,
    )
    raise RuntimeError(drafter_error.message) from normalized_exception
