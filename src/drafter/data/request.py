"""
The Request dataclass, describing a single client-to-server interaction
(a page visit, form submission, or component event).
"""

from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class Request:
    """
    Represents a request sent from the client to the server.

    Attributes:
        id: The unique identifier for this request.
        action: The action being performed (e.g., "click", "submit").
        url: The URL path being requested.
        kwargs: A dictionary of keyword arguments (form data) sent with the request.
        event: A dictionary of additional event information.
        dom_id: The DOM id of the element that triggered the request, if applicable.
        button_pressed: The name of the button that submitted the request, or an
            empty string if no button was involved.
        raw_payload: Optional provenance-tagged payload entries produced by the
            bridge; each entry is a dict with "name", "value", "source", and
            "source_detail" keys. When present, the router prefers these over
            the merged kwargs so it can report where each value came from.
    """

    REQUEST_COUNTER: ClassVar[int] = 0

    id: int = field(init=False)
    action: str
    url: str
    kwargs: dict
    event: dict
    dom_id: str = ""
    button_pressed: str = ""
    raw_payload: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Assign the next sequential request id."""
        type(self).REQUEST_COUNTER += 1
        self.id = type(self).REQUEST_COUNTER

    def to_json(self) -> dict[str, Any]:
        """Describe the request as a plain dictionary.

        Values are passed through as-is (callers that need strict JSON
        safety, like the error envelope, sanitize the result themselves);
        `button_pressed` may be a live DOM element, so it is reduced to a
        short string description.

        Returns:
            A dictionary with the request's fields.
        """
        button = self.button_pressed
        if button is not None and not isinstance(button, str):
            button = getattr(button, "id", None) or repr(button)
        return {
            "id": self.id,
            "action": self.action,
            "url": self.url,
            "kwargs": self.kwargs,
            "event": self.event,
            "dom_id": self.dom_id,
            "button_pressed": button,
            "raw_payload": self.raw_payload,
        }
