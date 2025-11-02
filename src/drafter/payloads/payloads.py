from typing import Any
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState


class ResponsePayload:
    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        return "<div>Default Response Payload: This should have been subclassed.</div>"

    def get_state_updates(self) -> tuple[bool, Any]:
        return False, None
