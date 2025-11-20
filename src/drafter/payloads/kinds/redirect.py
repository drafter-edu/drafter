from typing import Optional
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure
from drafter.data.request import Request
from drafter.router.routes import Router


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
    
    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> Optional[str]:
        # If there's a next_payload, render it; otherwise no content
        if self.next_payload:
            return self.next_payload.render(state, configuration)
        return None
    
    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        if not isinstance(self.target_route, str):
            return VerificationFailure(
                f"Redirect payload from {request.url} must have target_route as a string. "
                f"Found {type(self.target_route).__name__} instead."
            )
        
        # Check if the target route exists
        if not router.has_route(self.target_route):
            return VerificationFailure(
                f"Redirect payload from {request.url} references non-existent route: {self.target_route}"
            )
        
        # If there's a next_payload, verify it too
        if self.next_payload:
            return self.next_payload.verify(router, state, configuration, request)
        
        return None
    
    def get_state_updates(self) -> tuple[bool, any]:
        # If there's a next_payload, use its state updates
        if self.next_payload:
            return self.next_payload.get_state_updates()
        return False, None
