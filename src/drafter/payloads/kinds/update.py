from typing import Optional, Any
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure
from drafter.data.request import Request
from drafter.router.routes import Router


@dataclass
class Update(ResponsePayload):
    """
    An Update is a payload that will update the current page's state without
    reloading the entire page. This is useful for making small changes to the
    page dynamically.
    
    :param state_update: The new state or state changes to apply.
    """

    state_update: Any

    def get_state_updates(self) -> tuple[bool, Any]:
        return True, self.state_update

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> Optional[str]:
        return None
    
    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        if self.state_update is None:
            return VerificationFailure(
                f"Update payload from {request.url} must have a state_update. "
                f"Received None instead."
            )
        return None
