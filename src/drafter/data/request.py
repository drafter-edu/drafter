from dataclasses import dataclass


@dataclass
class Request:
    """
    Represents a request sent from the client to the server.
    
    :ivar id: The unique identifier for this request.
    :ivar action: The action being performed (e.g., "click", "submit").
    :ivar url: The URL path being requested.
    :ivar kwargs: A dictionary of keyword arguments (form data) sent with the request.
    :ivar event: A dictionary of additional event information.
    """

    id: int
    action: str
    url: str
    kwargs: dict
    event: dict
