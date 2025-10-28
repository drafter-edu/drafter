"""
Redirect payload for navigation to different URLs.

This module provides the Redirect class which represents a navigation
redirect to a different page or URL.
"""

from dataclasses import dataclass
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Redirect(ResponsePayload):
    """
    Represents a redirect to a different URL.

    Redirects cause the browser to navigate to a different page, either within
    the application or to an external URL.

    :ivar url: The URL to redirect to.
    :ivar external: Whether the redirect is to an external URL (outside the app).
    """

    url: str
    external: bool = False

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        """
        Renders the redirect as a meta refresh or JavaScript redirect.

        :param state: The current state of the site.
        :param configuration: The client server configuration.
        :return: HTML content that triggers the redirect.
        """
        # For now, use meta refresh for simplicity
        return f'<meta http-equiv="refresh" content="0; url={self.url}">'
