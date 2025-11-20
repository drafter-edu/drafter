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
        """
        Renders the payload to an HTML string. This is meant to then be injected
        into a page.
        """
        return None

    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        """
        Verifies that the payload is valid given the current state and configuration.

        :return: A VerificationFailure if the payload is invalid, otherwise None.
        """
        return None

    def format(
        self,
        state: SiteState,
        representation: str,
        configuration: ClientServerConfiguration,
    ) -> str:
        """
        Formats the payload for display in the history panel.
        Essentially, the result should be a `repr` that could be used to recreate
        the payload.
        """
        return ""

    def get_messages(
        self,
        state: SiteState,
        configuration: ClientServerConfiguration,
    ) -> list[Message]:
        """
        Gets any messages that should be sent to the client as part of this payload.
        """
        return []

    def get_state_updates(self) -> tuple[bool, Any]:
        """
        Gets any state updates that should be applied to the SiteState as part of this payload.
        """
        return False, None
