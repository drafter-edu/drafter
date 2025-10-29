"""
Update payload for state updates.

This module provides the Update class which represents a state update
without changing the displayed page content.
"""

from dataclasses import dataclass
from typing import Dict, Any
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Update(ResponsePayload):
    """
    Represents a state update without changing page content.

    Updates allow for modifying the state without triggering a full page
    re-render. This is useful for background operations or incremental
    state changes.

    :ivar state_updates: Dictionary mapping state field names to their new values.
    """

    state_updates: Dict[str, Any]

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        """
        Renders a minimal response indicating a state update.

        The actual state update is handled by the BridgeClient based on the
        state_updates field, not by rendering HTML.

        :param state: The current state of the site.
        :param configuration: The client server configuration.
        :return: Empty or minimal HTML content.
        """
        # State updates don't render content - they're handled specially by BridgeClient
        return ""
