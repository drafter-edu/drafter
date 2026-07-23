"""
Telemetry data structures for collecting debug and monitoring information.

Telemetry is information that gets collected from various parts of the system
(ClientServer, SiteState, AuditLogger, etc.) and sent to the Monitor for
aggregation and presentation.

Every telemetry event is a :class:`TelemetryRecord` (or a subclass with more
fields based on its ``kind``). Each record carries its own bookkeeping
:class:`TelemetryMetadata` and :class:`~drafter.data.correlation.Correlation`
context directly, rather than being wrapped in an envelope.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from drafter.data.correlation import Correlation
from drafter.data.errors import ErrorDetails
from drafter.version import CURRENT_DRAFTER_VERSION


@dataclass
class TelemetryMetadata:
    """
    Bookkeeping information attached to every telemetry record.

    Attributes:
        source: The source of the event, typically the component/module and the function/method name.
            For example, "client_server.handle_request".
        level: The telemetry level of the event ("info", "warning", or "error").
        id: A unique identifier for the telemetry record (auto-assigned).
        version: The version of the telemetry record structure.
        timestamp: The timestamp when the record was created.
    """

    source: str = ""
    level: str = "info"
    id: int = -1
    version: str = CURRENT_DRAFTER_VERSION
    timestamp: datetime = field(default_factory=datetime.now)

    IDS_COUNTER: ClassVar[int] = 0

    def __post_init__(self):
        if self.id == -1:
            type(self).IDS_COUNTER += 1
            self.id = type(self).IDS_COUNTER

    def to_json(self) -> dict[str, Any]:
        """
        Converts the TelemetryMetadata instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the TelemetryMetadata.
        """
        return {
            "source": self.source,
            "level": self.level,
            "id": self.id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TelemetryRecord:
    """
    Base class for all telemetry records published on the event bus.

    Subclasses add more fields based on their ``kind``.

    Attributes:
        kind: The kind of record (e.g. "RequestEvent", "UpdatedState"), used
            to dispatch the record to the right consumer.
        metadata: Bookkeeping information (source, level, id, version, timestamp).
        correlation: Correlation information for the event. This helps track where
            the event originated and its context.
    """

    kind: str = ""
    metadata: TelemetryMetadata = field(default_factory=TelemetryMetadata)
    correlation: Correlation = field(default_factory=Correlation)

    def to_json(self) -> dict[str, Any]:
        """
        Converts the TelemetryRecord instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the TelemetryRecord.
        """
        return {
            "kind": self.kind,
            "metadata": self.metadata.to_json(),
            "correlation": self.correlation.to_json(),
        }


@dataclass
class ErrorRecord(TelemetryRecord):
    """
    Telemetry record carrying a canonical :class:`ErrorDetails`.

    The record's ``kind`` is the error's stable, code-like id
    (e.g. ``request.route_not_found``).

    Attributes:
        error: The canonical error envelope being reported.
    """

    error: ErrorDetails | None = None

    def to_json(self) -> dict[str, Any]:
        """
        Converts the ErrorRecord instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the ErrorRecord, with the error
            envelope serialized (or None when no error is attached).
        """
        return {
            **super().to_json(),
            "error": self.error.to_json() if self.error is not None else None,
        }
