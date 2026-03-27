from typing import ClassVar
from dataclasses import dataclass, field


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
    """
    REQUEST_COUNTER: ClassVar[int] = 0

    id: int = field(init=False)
    action: str
    url: str
    kwargs: dict
    event: dict
    dom_id: str = ""
    button_pressed: str = ""

    def __post_init__(self):
        type(self).REQUEST_COUNTER += 1
        self.id = type(self).REQUEST_COUNTER
    