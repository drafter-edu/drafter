"""The `SimpleErrorPage` payload for reporting internal server errors."""

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
        self, state: SiteState, configuration: ClientServerConfiguration | None
    ) -> str:
        """Render the error as a plain `System Error: ...` string.

        The single static friendly sentence is deliberate: this payload must
        stay bulletproof, so it never consults the error explainer or any
        other rendering machinery.

        Args:
            state: Current application state (unused).
            configuration: Server configuration (unused).

        Returns:
            str: The error text.
        """
        return (
            "Drafter itself hit a problem while showing this page, so only a "
            "plain message is available. Reloading the application may help. "
            f"System Error: {self.message}"
        )
