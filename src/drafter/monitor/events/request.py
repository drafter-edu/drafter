"""
Request/Response/Outcome events for tracking page visits and server interactions.
"""

from dataclasses import dataclass
from typing import Any

from drafter.monitor.events.base import BaseEvent


@dataclass
class RequestEvent(BaseEvent):
    """
    Event emitted when a request is received.

    :ivar url: The URL being requested
    :ivar action: The action being performed
    :ivar args: Request arguments
    :ivar kwargs: Request keyword arguments
    :ivar request_id: Unique identifier for this request
    """

    url: str = ""
    action: str = ""
    args: str = ""
    kwargs: str = ""
    request_id: int = -1
    event_type: str = "RequestEvent"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "url": self.url,
            "action": self.action,
            "args": self.args,
            "kwargs": self.kwargs,
            "request_id": self.request_id,
        }


@dataclass
class ResponseEvent(BaseEvent):
    """
    Event emitted when a response is sent.

    :ivar status_code: HTTP status code
    :ivar payload_type: Type of the response payload
    :ivar body_length: Length of the response body
    :ivar has_errors: Whether the response has errors
    :ivar has_warnings: Whether the response has warnings
    :ivar duration_ms: Time taken to process the request in milliseconds
    :ivar response_id: Unique identifier for this response
    :ivar request_id: ID of the associated request
    """

    status_code: int = 200
    payload_type: str = ""
    body_length: int = 0
    has_errors: bool = False
    has_warnings: bool = False
    duration_ms: float = 0.0
    response_id: int = -1
    request_id: int = -1
    event_type: str = "ResponseEvent"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "status_code": self.status_code,
            "payload_type": self.payload_type,
            "body_length": self.body_length,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "duration_ms": self.duration_ms,
            "response_id": self.response_id,
            "request_id": self.request_id,
        }


@dataclass
class OutcomeEvent(BaseEvent):
    """
    Event emitted when an outcome is received from the client.

    :ivar message: Outcome message
    :ivar success: Whether the outcome was successful
    :ivar outcome_id: Unique identifier for this outcome
    :ivar response_id: ID of the associated response
    """

    message: str = ""
    success: bool = True
    outcome_id: int = -1
    response_id: int = -1
    event_type: str = "OutcomeEvent"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "message": self.message,
            "success": self.success,
            "outcome_id": self.outcome_id,
            "response_id": self.response_id,
        }


@dataclass
class PageVisitEvent(BaseEvent):
    """
    Event that combines request, response, and outcome for a complete page visit.

    :ivar url: The URL visited
    :ivar function_name: Name of the function called
    :ivar arguments: String representation of arguments
    :ivar status_code: Response status code
    :ivar duration_ms: Total duration in milliseconds
    :ivar timestamp: ISO timestamp of the visit
    :ivar button_pressed: Name of button pressed (if any)
    """

    url: str = ""
    function_name: str = ""
    arguments: str = ""
    status_code: int = 200
    duration_ms: float = 0.0
    timestamp: str = ""
    button_pressed: str = ""
    event_type: str = "PageVisitEvent"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "url": self.url,
            "function_name": self.function_name,
            "arguments": self.arguments,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "button_pressed": self.button_pressed,
        }
