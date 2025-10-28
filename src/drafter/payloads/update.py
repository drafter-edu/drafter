"""
Update payload for targeted DOM updates.

This module provides the Update class which represents a targeted update
to specific elements on the page without replacing the entire content.
"""

from dataclasses import dataclass
from typing import Dict
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Update(ResponsePayload):
    """
    Represents targeted updates to specific DOM elements.

    Updates allow for surgical changes to the page by specifying which
    elements to update and what their new content should be.

    :ivar updates: Dictionary mapping element IDs to their new HTML content.
    """

    updates: Dict[str, str]

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        """
        Renders the update instructions.

        Note: This is a simplified implementation. In a real implementation,
        the BridgeClient would parse these updates and apply them to the DOM.

        :param state: The current state of the site.
        :param configuration: The client server configuration.
        :return: HTML content representing the updates.
        """
        # This is a placeholder - the actual updates would be handled by the BridgeClient
        content = ["<div class='drafter-update' style='display:none;'>"]
        for element_id, html_content in self.updates.items():
            content.append(f"<div data-target='{element_id}'>{html_content}</div>")
        content.append("</div>")
        return "\n".join(content)
