from dataclasses import dataclass
from typing import Any

from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class BasePage(ResponsePayload):
    """
    Base class for all page payloads.
    """

    def render_debug(
        self, state: SiteState, configuration: ClientServerConfiguration
    ) -> str:
        return self.render(state, configuration)
