"""
Audit helpers for publishing telemetry onto the main event bus.

Provides `log_error` for reporting canonical ErrorDetails envelopes as
ErrorRecords, and `log_record` for stamping and publishing general
telemetry records.
"""

from drafter.data.correlation import Correlation
from drafter.data.errors import (
    ErrorDetails,
)
from drafter.data.telemetry import ErrorRecord, TelemetryMetadata, TelemetryRecord


def log_error(
    envelope: ErrorDetails,
    source: str,
    causation_id: int | None = None,
) -> ErrorDetails:
    """Emit canonical telemetry for an ErrorDetails as an ErrorRecord.

    Publishes an ErrorRecord whose kind is the envelope's stable id
    and which carries the canonical ErrorDetails itself.

    Args:
        envelope: The canonical error envelope to report.
        source: The component/function reporting the failure.
        causation_id: Optional id of the event that caused this one.

    Returns:
        The canonical envelope that was published.
    """
    from drafter.client_server.commands import get_main_event_bus

    if envelope.severity == "warning":
        level = "warning"
    elif envelope.severity == "info":
        level = "info"
    else:
        # "error" and "critical" both map to the "error" telemetry level;
        # the finer severity remains available on the envelope itself.
        level = "error"
    get_main_event_bus().publish(
        ErrorRecord(
            kind=envelope.id,
            metadata=TelemetryMetadata(source=source, level=level),
            correlation=envelope.context,
            error=envelope,
        )
    )
    return envelope


def log_record(
    record: TelemetryRecord,
    source: str,
    causation_id: int | None = None,
    request_id: int | None = None,
    response_id: int | None = None,
    dom_id: str | None = None,
    route: str | None = None,
) -> TelemetryRecord:
    """Fill in a record's metadata/correlation and publish it on the main bus.

    Args:
        record: The telemetry record to publish.
        source: The component/function emitting the record.
        causation_id: Optional id of the event that caused this one.
        request_id: Optional id of the associated request.
        response_id: Optional id of the associated response.
        dom_id: Optional id of the associated DOM element.
        route: Optional route name/url associated with the record.

    Returns:
        The record that was published.
    """
    from drafter.client_server.commands import get_main_event_bus

    record.metadata = TelemetryMetadata(source=source, level="info")
    record.correlation = Correlation(
        causation_id=causation_id,
        route=route,
        request_id=request_id,
        response_id=response_id,
        dom_id=dom_id,
    )
    get_main_event_bus().publish(record)
    return record
