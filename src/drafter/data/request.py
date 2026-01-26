from dataclasses import dataclass


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

    id: int
    action: str
    url: str
    kwargs: dict
    event: dict
    dom_id: str = ""
