from typing import Optional
from dataclasses import dataclass
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class SimpleErrorPage(ResponsePayload):
    message: str

    def render(
        self, state: SiteState, configuration: Optional[ClientServerConfiguration]
    ) -> str:
        return f"System Error: {self.message}"
