from typing import Any, Optional
from drafter.data.channel import Message
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure


class ResponsePayload:
    def render(
        self, state: SiteState, configuration: ClientServerConfiguration
    ) -> Optional[str]:
        return None

    def verify(
        self, state: SiteState, configuration: ClientServerConfiguration
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
