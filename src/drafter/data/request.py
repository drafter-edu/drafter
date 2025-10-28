from dataclasses import dataclass


@dataclass
class Request:
    """
    Represents a request sent from the client to the server.
    """

    id: int
    action: str
    url: str
    args: list
    kwargs: dict
    event: dict
