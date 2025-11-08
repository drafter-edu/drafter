from typing import Any, Optional
from drafter.data.channel import Message
from drafter.data.request import Request
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure
from drafter.router.routes import Router


class ResponsePayload:
    def render(
        self, state: SiteState, configuration: ClientServerConfiguration
    ) -> Optional[str]:
        return None

    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        return None

    def get_messages(
        self,
        state: SiteState,
        configuration: ClientServerConfiguration,
    ) -> list[Message]:
        return []

    def get_state_updates(self) -> tuple[bool, Any]:
        return False, None
