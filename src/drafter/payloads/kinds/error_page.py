"""The `SimpleErrorPage` payload for reporting internal server errors."""

from typing import Optional
from dataclasses import dataclass
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class SimpleErrorPage(ResponsePayload):
    """Minimal payload that renders a plain error message.

    Used when the server needs to report a system error without any of the
    usual page rendering machinery.

    Attributes:
        message: Description of the error to display.
    """

    message: str

    def render(
        self, state: SiteState, configuration: Optional[ClientServerConfiguration]
    ) -> str:
        """Render the error as a plain `System Error: ...` string.

        Args:
            state: Current application state (unused).
            configuration: Server configuration (unused).

        Returns:
            str: The error text.
        """
        return f"System Error: {self.message}"
