"""
Download payload for file downloads.

This module provides the Download class which represents a file download
response that triggers a file download in the browser.
"""

from dataclasses import dataclass
from typing import Union
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Download(ResponsePayload):
    """
    Represents a file download response.

    Downloads trigger the browser to download a file, either from binary data
    or from a text string.

    :ivar content: The content of the file to download (bytes or string).
    :ivar filename: The suggested filename for the download.
    :ivar mime_type: The MIME type of the file (e.g., "text/plain", "application/pdf").
    """

    content: Union[bytes, str]
    filename: str = "download.txt"
    mime_type: str = "text/plain"

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        """
        Renders the download trigger.

        Note: This is a simplified implementation. In a real implementation,
        the BridgeClient would need to handle this specially to trigger an
        actual download.

        :param state: The current state of the site.
        :param configuration: The client server configuration.
        :return: HTML content indicating a download.
        """
        # This is a placeholder - the actual download would be handled by the BridgeClient
        return f"<div>Download triggered: {self.filename}</div>"
