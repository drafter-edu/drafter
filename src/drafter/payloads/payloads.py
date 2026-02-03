from typing import Any, Optional, Union, TYPE_CHECKING
from drafter.data.channel import Message
from drafter.data.request import Request
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure
from drafter.router.routes import Router

if TYPE_CHECKING:
    from drafter.payloads.target import Target


class ResponsePayload:
    """Base class for all payload types sent from routes to the client.

    Defines the interface for rendering, verifying, formatting, and extracting
    state updates and client-side messages from payloads. Subclasses should
    override methods as needed for their specific behavior.
    """

    def render(
        self, state: SiteState, configuration: ClientServerConfiguration
    ) -> Optional[str]:
        """Render the payload to HTML for browser display.

        Args:
            state: Current application state.
            configuration: Server configuration.

        Returns:
            str or None: HTML string to inject into page, or None.
        """
        return None

    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        """Verify payload validity before rendering.

        Args:
            router: Server router for validation context.
            state: Current application state.
            configuration: Server configuration.
            request: Associated request for context.

        Returns:
            VerificationFailure or None: Failure object if invalid, else None.
        """
        return None

    def format(
        self,
        state: SiteState,
        representation: str,
        configuration: ClientServerConfiguration,
    ) -> str:
        """Format payload for history panel display (debug output).

        Should produce a repr-like string that could recreate the payload.

        Args:
            state: Current application state.
            representation: String representation of route arguments.
            configuration: Server configuration.

        Returns:
            str: Formatted representation of the payload.
        """
        return ""

    def get_messages(
        self,
        state: SiteState,
        configuration: ClientServerConfiguration,
    ) -> list[Message]:
        """Extract channel messages to execute on the client.

        Messages may contain CSS, JavaScript, or other client-side directives.

        Args:
            state: Current application state.
            configuration: Server configuration.

        Returns:
            list[Message]: Messages to send to the client.
        """
        return []

    def get_state_updates(self) -> tuple[bool, Any]:
        """Extract state updates to apply after rendering.

        Args:
            (None)

        Returns:
            Tuple of (has_updates: bool, updated_state: Any).
        """
        return False, None

    def is_redirect(self) -> bool:
        """Check if this payload triggers a redirect.

        Returns:
            bool: True if this is a redirect payload.
        """
        return False

    def get_redirect(self) -> tuple[str, Optional[dict]]:
        """Retrieve redirect target and optional query arguments.

        Returns:
            Tuple of (target_url: str, args_dict or None).
        """
        return "", None

    def get_target(self, request: Request) -> "Optional[Target]":
        """Get the Target for fragment updates.

        Returns:
            Target instance or None: Target object for fragment replacement, or None for full page.
        """
        return None
