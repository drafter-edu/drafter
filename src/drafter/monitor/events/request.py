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
    :ivar url: The URL being requested
    :ivar action: The action being performed
    :ivar kwargs: Request keyword arguments
    :ivar event: Additional event information
    :ivar request_id: Unique identifier for this request
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

    :ivar request_id: Unique identifier for this request
    :ivar representation: String representation of the parsed request
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

