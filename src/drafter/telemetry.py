"""
Telemetry data structures for collecting debug and monitoring information.

Telemetry is information that gets collected from various parts of the system
(ClientServer, SiteState, AuditLogger, etc.) and sent to the Monitor for
aggregation and presentation.
"""
from dataclasses import dataclass
from typing import Any, Optional, Dict, List
from datetime import datetime


@dataclass
class PageVisitTelemetry:
    """
    Telemetry data for a complete request/response/outcome cycle.
    
    Uses the actual Request, Response, and Outcome objects instead of
    creating redundant copies of their data.
    
    :ivar request: The actual Request object
    :ivar request_timestamp: When the request was received
    :ivar response: The actual Response object (if completed)
    :ivar response_timestamp: When the response was sent (if completed)
    :ivar outcome: The actual Outcome object (if received)
    :ivar outcome_timestamp: When the outcome was received (if received)
    :ivar state_snapshot: Snapshot of state after this visit
    :ivar duration_ms: Duration from request to response in milliseconds
    """
    request: Any  # Request object
    request_timestamp: datetime
    response: Optional[Any] = None  # Response object
    response_timestamp: Optional[datetime] = None
    outcome: Optional[Any] = None  # Outcome object
    outcome_timestamp: Optional[datetime] = None
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
