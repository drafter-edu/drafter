"""Shared error-handling helpers for bridge-side runtime failures.

These helpers centralize exception normalization and telemetry reporting so
bridge modules can avoid ad hoc ``print`` + ``raise`` patterns.

All reports are envelope-first: a canonical :class:`ErrorDetails`
(category ``bridge``) is created before telemetry is emitted, mirroring the
server-side visit lifecycle. Bridge lifecycle ``phase`` tags are ``setup``,
``navigation``, ``channel_execution``, and ``event_dispatch``.
"""

from typing import Any

from drafter.data.error_explainer import explain
from drafter.data.errors import (
    CATEGORY_BRIDGE,
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    STATUS_ERROR,
    Correlation,
    ErrorDetails,
    envelope_from_exception,
)
from drafter.monitor.audit import log_error


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
    data: dict[str, Any] | None = None,
    exception: Any | None = None,
    request_id: int | None = None,
    response_id: int | None = None,
    dom_id: str | None = None,
    route: str | None = None,
    phase: str | None = None,
    severity: str = SEVERITY_ERROR,
    status_code: str | None = None,
    recoverable: bool = True,
) -> ErrorDetails:
    """Build a canonical bridge envelope, emit telemetry, and return the event.

    The envelope is created first (category ``bridge``, correlation context
    from the keyword arguments), then :func:`log_error` publishes it.
    Falls back to returning the in-memory envelope if telemetry logging itself
    fails.

    Args:
        event_type: Stable, code-like id (e.g. ``bridge.redirect_loop_detected``).
        message: Human-safe message.
        source: The component/function reporting the failure.
        details: Developer-focused free-text details.
        data: Structured, JSON-safe details (sanitized on construction).
        exception: Originating exception or thrown value, if any.
        request_id: Associated request id, if known.
        response_id: Associated response id, if known.
        dom_id: Associated DOM element id, if known.
        route: Associated route, if known.
        phase: Bridge lifecycle phase (setup, navigation, channel_execution,
            event_dispatch).
        severity: Canonical severity (default ``error``).
        status_code: Symbolic status string; defaults to STATUS_ERROR.
        recoverable: Whether the bridge can continue after this failure.
    """
    normalized_exception = (
        normalize_bridge_exception(exception) if exception is not None else None
    )
    context = Correlation(
        route=route,
        request_id=request_id,
        response_id=response_id,
        dom_id=dom_id,
        phase=phase,
    )
    resolved_status = status_code if status_code is not None else STATUS_ERROR
    if normalized_exception is not None:
        envelope = envelope_from_exception(
            normalized_exception,
            event_type,
            CATEGORY_BRIDGE,
            message=message,
            details=details,
            data=data,
            severity=severity,
            context=context,
            status_code=resolved_status,
            recoverable=recoverable,
        )
    else:
        explanation = explain(None, event_type, CATEGORY_BRIDGE)
        envelope = ErrorDetails(
            id=event_type,
            category=CATEGORY_BRIDGE,
            message=message,
            severity=severity,
            details=details,
            data=data or {},
            friendly_title=explanation.title,
            friendly_message=explanation.message,
            friendly_steps=explanation.steps,
            context=context,
            status_code=resolved_status,
            recoverable=recoverable,
        )
    try:
        return log_error(envelope, source)
    except Exception:
        return envelope


def report_bridge_warning(
    event_type: str,
    message: str,
    source: str,
    details: str,
    *,
    exception: Any | None = None,
    request_id: int | None = None,
    response_id: int | None = None,
    dom_id: str | None = None,
    route: str | None = None,
    phase: str | None = None,
    status_code: str | None = None,
) -> ErrorDetails:
    """Report a non-fatal bridge issue as a canonical warning.

    Same contract as :func:`report_bridge_error` with warning severity;
    use for degraded-but-recovered situations (e.g. fallbacks applied).
    """
    return report_bridge_error(
        event_type,
        message,
        source,
        details,
        exception=exception,
        request_id=request_id,
        response_id=response_id,
        dom_id=dom_id,
        route=route,
        phase=phase,
        severity=SEVERITY_WARNING,
        status_code=status_code,
    )


def raise_bridge_system_error(
    event_type: str,
    message: str,
    source: str,
    details: str,
    *,
    exception: Any | None = None,
    request_id: int | None = None,
    response_id: int | None = None,
    dom_id: str | None = None,
    route: str | None = None,
    phase: str | None = None,
    status_code: str | None = None,
) -> None:
    """Log and raise a normalized RuntimeError for bridge system failures.

    This function always raises: the failure is first reported through
    `report_bridge_error` (with `recoverable=False`), then a RuntimeError
    carrying the envelope's message is raised, chained from the normalized
    originating exception if one was given.

    Args:
        event_type: Stable, code-like id (e.g. ``client.form_root_missing``).
        message: Human-safe message; becomes the RuntimeError's message.
        source: The component/function reporting the failure.
        details: Developer-focused details.
        exception: Originating exception or thrown value, if any;
            normalized and chained as the RuntimeError's cause.
        request_id: Associated request id, if known.
        response_id: Associated response id, if known.
        dom_id: Associated DOM element id, if known.
        route: Associated route, if known.
        phase: Bridge lifecycle phase (setup, navigation,
            channel_execution, event_dispatch).
        status_code: Symbolic status string; defaults to STATUS_ERROR.

    Raises:
        RuntimeError: Always, with the logged envelope's message, chained
            from the normalized originating exception when one was given.
    """
    normalized_exception = (
        normalize_bridge_exception(exception) if exception is not None else None
    )
    envelope = report_bridge_error(
        event_type,
        message,
        source,
        details,
        exception=normalized_exception,
        request_id=request_id,
        response_id=response_id,
        dom_id=dom_id,
        route=route,
        phase=phase,
        status_code=status_code,
        recoverable=False,
    )
    raise RuntimeError(envelope.message) from normalized_exception
