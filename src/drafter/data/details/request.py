"""
Request/Response events for tracking page visits and server interactions.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from drafter.data.errors import STATUS_OK
from drafter.data.telemetry import TelemetryRecord


@dataclass
class RequestEvent(TelemetryRecord):
    """
    Event emitted when a request is received.

    Attributes:
        url: The URL being requested
        action: The action being performed
        kwargs: String representation of the request keyword arguments
        kwargs_json: JSON encoding of the request keyword arguments, or ""
            when they are not JSON-serializable. Lets the debug history's
            Revisit button rebuild the request even after the in-memory
            request log has been reset or aged out.
        event: String representation of the additional event information
        request_id: Unique identifier for this request
        kind: Event-type discriminator, always "RequestEvent"
    """

    url: str = ""
    action: str = ""
    kwargs: str = ""
    kwargs_json: str = ""
    event: str = ""
    request_id: int = -1
    kind: str = "RequestEvent"

    def to_json(self) -> dict[str, Any]:
        """
        Converts the RequestEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
            "url": self.url,
            "action": self.action,
            "kwargs": self.kwargs,
            "kwargs_json": self.kwargs_json,
            "event": self.event,
            "request_id": self.request_id,
        }

    @classmethod
    def from_request(cls, request) -> "RequestEvent":
        """
        Builds a RequestEvent summarizing the given request.

        Args:
            request: The Request to summarize; its kwargs and event dicts
                are captured as string representations (plus a JSON
                encoding of kwargs when possible, for replay).

        Returns:
            A new RequestEvent populated from the request.
        """
        try:
            kwargs_json = json.dumps(request.kwargs) if request.kwargs else "{}"
        except Exception:
            kwargs_json = ""
        return cls(
            url=request.url,
            action=request.action,
            kwargs=str(request.kwargs),
            kwargs_json=kwargs_json,
            event=str(request.event),
            request_id=request.id,
        )


# TODO: Also track unused arguments, unmatched arguments, and
#       button-namespace usage in RequestParseEvent.
@dataclass
class RequestParseEvent(TelemetryRecord):
    """
    Event emitted when a request is parsed.

    Files and images get special handling so they can be
    rendered properly in the client, and also in the history.

    Attributes:
        request_id: Unique identifier for this request
        representation: String representation of the parsed request
        arguments: Per-parameter provenance dicts (name, source,
            source_detail, value, expected_type, converted, changed)
            describing where each bound argument came from
        kind: Event-type discriminator, always "RequestParseEvent"
    """

    request_id: int = -1
    representation: str = ""
    arguments: list[dict] = field(default_factory=list)
    kind: str = "RequestParseEvent"

    def to_json(self) -> dict[str, Any]:
        """
        Converts the RequestParseEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
            "request_id": self.request_id,
            "representation": self.representation,
            "arguments": self.arguments,
        }


@dataclass
class ResponseEvent(TelemetryRecord):
    """
    Event emitted when a response is sent.

    Attributes:
        status_code: Symbolic response status (see drafter.data.errors.STATUSES)
        payload_type: Type of the response payload
        body_length: Length of the response body
        has_errors: Whether the response has errors
        has_warnings: Whether the response has warnings
        duration_ms: Time taken to process the request in milliseconds
        response_id: Unique identifier for this response
        request_id: ID of the associated request
        formatted_page_content: The rendered HTML content of the page
            (falls back to the raw response body when no formatted body
            is available)
        kind: Event-type discriminator, always "ResponseEvent"
    """

    status_code: str = STATUS_OK
    payload_type: str = ""
    body_length: int = 0
    has_errors: bool = False
    has_warnings: bool = False
    duration_ms: float = 0.0
    response_id: int = -1
    request_id: int = -1
    formatted_page_content: str = ""
    kind: str = "ResponseEvent"

    def to_json(self) -> dict[str, Any]:
        """
        Converts the ResponseEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
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
        """
        Builds a ResponseEvent summarizing the given response.

        Args:
            response: The Response to summarize.
            formatted_body: The rendered HTML page content; the raw
                response body is used instead when this is empty.
            duration_ms: Time taken to process the request in milliseconds.

        Returns:
            A new ResponseEvent populated from the response.
        """
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
