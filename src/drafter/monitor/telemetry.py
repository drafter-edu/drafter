"""
Telemetry data structures for collecting debug and monitoring information.

Telemetry is information that gets collected from various parts of the system
(ClientServer, SiteState, AuditLogger, etc.) and sent to the Monitor for
aggregation and presentation.
"""

from dataclasses import dataclass
from typing import Any, Optional, Dict
from datetime import datetime

from drafter.monitor.events.base import BaseEvent


@dataclass
class TelemetryCorrelation:
    """
    Correlation information for telemetry events.

    :ivar causation_id: The ID of the causation event; if this event was caused by another event.
    :ivar route: The route name/url associated with the event
    :ivar request_id: The ID of the associated request
    :ivar response_id: The ID of the associated response
    :ivar outcome_id: The ID of the associated outcome
    :ivar dom_id: The ID of the associated DOM element if this came from the Bridge Client.
    """

    causation_id: Optional[int] = None
    route: Optional[str] = None
    request_id: Optional[int] = None
    response_id: Optional[int] = None
    outcome_id: Optional[int] = None
    dom_id: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        """
        Converts the TelemetryCorrelation instance to a JSON-serializable dictionary.

        :return: A dictionary representation of the TelemetryCorrelation.
        """
        return {
            "causation_id": self.causation_id,
            "route": self.route,
            "request_id": self.request_id,
            "response_id": self.response_id,
            "outcome_id": self.outcome_id,
            "dom_id": self.dom_id,
        }


@dataclass
class TelemetryEvent:
    """
    A telemetry event that should be published for anyone listening.

    :ivar event_type: The type of telemetry event. This is a dot-separated string indicating
        the category and subcategory of the event. Major categories include "logger", "request",
        "response", "outcome", "state", "config", "dom".
    :ivar correlation: Correlation information for the event. This helps track where the event
        originated and its context.
    :ivar source: The source of the event, typically the component/module and the function/method name.
        For example, "client_server.handle_request".
    :ivar id: A unique identifier for the telemetry event.
    :ivar version: The version of the telemetry event structure.
    :ivar level: The severity level of the event (e.g., "info", "warning", "error").
    :ivar timestamp: The timestamp when the event was created.
    :ivar data: Additional data associated with the event. This can be any relevant information
        that provides context about the event. Must be JSON-serializable. The exact
        structure should be defined based on the event_type.
    """

    event_type: str
    correlation: TelemetryCorrelation
    source: str
    id: int = -1
    version: str = "0.0.1"
    level: Optional[str] = "info"
    timestamp: datetime = datetime.now()
    data: Optional[BaseEvent] = None

    IDS_COUNTER: int = 0

    def __post_init__(self):
        type(self).IDS_COUNTER += 1
        self.id = type(self).IDS_COUNTER

    def to_json(self) -> Dict[str, Any]:
        """
        Converts the TelemetryEvent instance to a JSON-serializable dictionary.

        :return: A dictionary representation of the TelemetryEvent.
        """
        return {
            "event_type": self.event_type,
            "correlation": self.correlation.to_json(),
            "source": self.source,
            "id": self.id,
            "version": self.version,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data.to_json() if self.data is not None else None,
        }
