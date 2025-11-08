from typing import Optional
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Redirect(ResponsePayload):
    """
    A Redirect is a payload that will redirect the user to a new route.

    Often, it is simpler to simply call a different route function inline.
    However, that will not change the back/forward history of the browser.
    A Redirect payload will cause the browser to navigate to a new route,
    updating the history as appropriate.

    :param target_route: The route to redirect to.
    :param next_payload: An optional payload to send after the redirect.
        Usually a Page payload.
    """

    target_route: str
    next_payload: Optional[ResponsePayload] = None
