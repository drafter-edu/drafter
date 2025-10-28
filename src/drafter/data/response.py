from dataclasses import dataclass, field
from drafter.data.errors import DrafterError, DrafterWarning
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Response:
    """
    Represents a response sent from the server to the client.

    Status codes loosely follow HTTP status code conventions.
    - 1xx: Informational (not used currently)
    - 2xx: Success
    - 3xx: Redirects (not used currently)
    - 4xx: User developer errors (i.e., in the route itself)
    - 5xx: BridgeClient errors
    - 6xx: ClientServer errors
    - 7xx: AppServer/BuildServer errors

    :ivar payload: The page content to send to the client.
    :ivar status_code: The status code of the response.
    :ivar message: A human-readable message associated with the response.
    :ivar body: The full HTML body of the response, which will be injected directly into the site's frame.
    :ivar channels: A dictionary of channels for additional communication. Common
        channels include "audio", "before", and "after". The latter two are used to
        send script tags to be executed before and after the main content is rendered.
    :ivar errors: A list of DrafterError instances representing errors that occurred.
    :ivar warnings: A list of DrafterWarning instances representing warnings that occurred.
    :ivar metadata: A dictionary of additional metadata associated with the response.
    """

    id: int
    request_id: int
    payload: ResponsePayload
    status_code: int = 200
    message: str = "OK"
    body: str = ""
    channels: dict = field(default_factory=dict)
    errors: list[DrafterError] = field(default_factory=list)
    warnings: list[DrafterWarning] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
