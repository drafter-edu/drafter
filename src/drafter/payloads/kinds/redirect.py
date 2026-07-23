from typing import Any, Optional
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Redirect(ResponsePayload):
    """
    A Redirect is a payload that will redirect the user to a new route.

    Often, it is simpler to simply call a different route function inline.
    However, that will not change the back/forward history of the browser.
    A Redirect payload will cause the browser to navigate to a new route,
    updating the history as appropriate. In other words, this is like a proper
    version of a function call that the client is aware of.

    Args:
        target_route: The route to redirect to.
        state_update: Optional new state to apply before redirecting; if None,
            the state is left unchanged.
        **kwargs: Any additional keyword arguments are passed to the target
            route as its arguments (stored in the `arguments` attribute).
    """

    target_route: str
    state_update: Optional[Any]
    arguments: Optional[dict] = None

    def __init__(self, target_route: str, state_update: Optional[Any] = None, **kwargs):
        self.target_route = target_route
        self.state_update = state_update
        self.arguments = kwargs if kwargs else None

    def is_redirect(self) -> bool:
        return True

    def get_state_updates(self) -> tuple[bool, Any]:
        return self.state_update is not None, self.state_update

    def get_redirect(self) -> tuple[str, Optional[dict]]:
        return self.target_route, self.arguments
