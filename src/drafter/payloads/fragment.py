"""
Fragment payload for partial page updates.

This module provides the Fragment class which represents a partial update
to the page, allowing for more efficient updates without reloading the entire page.
"""

from dataclasses import dataclass
from typing import Any
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Fragment(ResponsePayload):
    """
    Represents a fragment of content that can be used to update part of a page.

    Fragments allow for partial page updates, which can be more efficient than
    reloading the entire page. They contain HTML content that will replace or
    update a specific part of the DOM.

    :ivar content: The HTML content of the fragment.
    :ivar target_id: Optional DOM element ID to target for the update.
    """

    content: str
    target_id: str = ""

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        """
        Renders the fragment content.

        :param state: The current state of the site.
        :param configuration: The client server configuration.
        :return: The HTML content of the fragment.
        """
        return self.content
