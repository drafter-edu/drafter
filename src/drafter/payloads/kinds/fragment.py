from typing import Optional
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure
from drafter.data.request import Request
from drafter.router.routes import Router


@dataclass
class Fragment(ResponsePayload):
    """
    A Fragment is a payload that will render a fragment of HTML to be injected
    into an existing page, rather than a full page by itself.
    
    :param html: The HTML content to be rendered as a fragment.
    """

    html: str

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> Optional[str]:
        return self.html
    
    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        if not isinstance(self.html, str):
            return VerificationFailure(
                f"Fragment payload from {request.url} must have html as a string. "
                f"Found {type(self.html).__name__} instead."
            )
        return None
