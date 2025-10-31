"""
Telemetry data structures for collecting debug and monitoring information.

Telemetry is information that gets collected from various parts of the system
(ClientServer, SiteState, AuditLogger, etc.) and sent to the Monitor for
aggregation and presentation.
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime


@dataclass
class RequestTelemetry:
    """
    Telemetry data for a single request.
    
    :ivar request_id: Unique identifier for the request
    :ivar timestamp: When the request was received
    :ivar url: The URL being requested
    :ivar action: The action being performed
    :ivar args: Positional arguments
    :ivar kwargs: Keyword arguments
    :ivar event: Event information from the client
    """
    request_id: int
    timestamp: datetime
    url: str
    action: str
    args: List[Any]
    kwargs: Dict[str, Any]
    event: Dict[str, Any]


@dataclass
class ResponseTelemetry:
    """
    Telemetry data for a single response.
    
    :ivar response_id: Unique identifier for the response
    :ivar request_id: The request this is responding to
    :ivar timestamp: When the response was sent
    :ivar status_code: HTTP-like status code
    :ivar message: Human-readable status message
    :ivar payload_type: Type of the response payload
    :ivar body_length: Length of the rendered HTML body
    :ivar has_errors: Whether the response contains errors
    :ivar has_warnings: Whether the response contains warnings
    :ivar channels: Names of active channels in the response
    """
    response_id: int
    request_id: int
    timestamp: datetime
    status_code: int
    message: str
    payload_type: str
    body_length: int
    has_errors: bool
    has_warnings: bool
    channels: List[str]


@dataclass
class OutcomeTelemetry:
    """
    Telemetry data for a single outcome.
    
    :ivar outcome_id: Unique identifier for the outcome
    :ivar request_id: The original request
    :ivar response_id: The response this is acknowledging
    :ivar timestamp: When the outcome was received
    :ivar status_code: Status code from the client
    :ivar message: Human-readable message from client
    :ivar has_errors: Whether the outcome contains errors
    :ivar has_warnings: Whether the outcome contains warnings
    :ivar has_info: Whether the outcome contains info messages
    """
    outcome_id: int
    request_id: int
    response_id: int
    timestamp: datetime
    status_code: int
    message: str
    has_errors: bool
    has_warnings: bool
    has_info: bool


@dataclass
class PageVisitTelemetry:
    """
    Telemetry data for a complete request/response/outcome cycle.
    
    :ivar request: Request telemetry
    :ivar response: Response telemetry (if completed)
    :ivar outcome: Outcome telemetry (if received)
    :ivar state_snapshot: Snapshot of state after this visit
    :ivar duration_ms: Duration from request to response in milliseconds
    """
    request: RequestTelemetry
    response: Optional[ResponseTelemetry] = None
    outcome: Optional[OutcomeTelemetry] = None
    state_snapshot: Any = None
    duration_ms: Optional[float] = None


@dataclass
class MonitorSnapshot:
    """
    A complete snapshot of the monitor's state at a point in time.
    
    :ivar timestamp: When this snapshot was taken
    :ivar page_visits: History of page visits
    :ivar current_state: Current state of the site
    :ivar initial_state: Initial state of the site
    :ivar routes: Available routes
    :ivar errors: All errors logged
    :ivar warnings: All warnings logged
    :ivar info: All info messages logged
    :ivar server_config: Server configuration details
    """
    timestamp: datetime
    page_visits: List[PageVisitTelemetry]
    current_state: Any
    initial_state: Any
    routes: Dict[str, Any]
    errors: List[Any]
    warnings: List[Any]
    info: List[Any]
    server_config: Dict[str, Any]
