"""
Request/Response events for tracking page visits and server interactions.
"""

from dataclasses import dataclass
from typing import Any

from drafter.monitor.events.base import BaseEvent


@dataclass
class RequestEvent(BaseEvent):
    """
    Event emitted when a request is received.

    Attributes:
        url: The URL being requested
        action: The action being performed
        kwargs: Request keyword arguments
        event: Additional event information
        request_id: Unique identifier for this request
    """

    url: str = ""
    action: str = ""
    kwargs: str = ""
    event: str = ""
    request_id: int = -1
    event_type: str = "RequestEvent"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "url": self.url,
            "action": self.action,
            "kwargs": self.kwargs,
            "event": self.event,
            "request_id": self.request_id,
        }

    @classmethod
    def from_request(cls, request) -> "RequestEvent":
        return cls(
            url=request.url,
            action=request.action,
            kwargs=str(request.kwargs),
            event=str(request.event),
            request_id=request.id,
        )


@dataclass
class RequestParseEvent(BaseEvent):
    """
    Event emitted when a request is parsed.

    TODO: Also track argument type changes, unused arguments, unmatched arguments, etc.
    TODO: if a button namespace was used,

    Files and images get special handling so they can be
    rendered properly in the client, and also in the history.

    Attributes:
        request_id: Unique identifier for this request
        representation: String representation of the parsed request
    """

    request_id: int = -1
    representation: str = ""
    event_type: str = "RequestParseEvent"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "request_id": self.request_id,
            "representation": self.representation,
        }


@dataclass
class ResponseEvent(BaseEvent):
    """
    Event emitted when a response is sent.

    Attributes:
        status_code: HTTP status code
        payload_type: Type of the response payload
        body_length: Length of the response body
        has_errors: Whether the response has errors
        has_warnings: Whether the response has warnings
        duration_ms: Time taken to process the request in milliseconds
        response_id: Unique identifier for this response
        request_id: ID of the associated request
    """

    status_code: int = 200
    payload_type: str = ""
    body_length: int = 0
    has_errors: bool = False
    has_warnings: bool = False
    duration_ms: float = 0.0
    response_id: int = -1
    request_id: int = -1
    formatted_page_content: str = ""
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
            "formatted_page_content": self.formatted_page_content,
        }

    @classmethod
    def from_response(
        cls, response, formatted_body: str, duration_ms: float
    ) -> "ResponseEvent":
        return cls(
            status_code=response.status_code,
            payload_type=type(response.payload).__name__,
            body_length=len(response.body) if response.body else 0,
            has_errors=bool(response.errors),
            has_warnings=bool(response.warnings),
            duration_ms=duration_ms,
            response_id=response.id,
            request_id=response.request_id,
            formatted_page_content=formatted_body or response.body or "",
        )
