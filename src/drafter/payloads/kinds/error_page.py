from typing import Optional
from dataclasses import dataclass
from drafter.config.client_server import ClientServerConfiguration
from drafter.monitor.events.errors import DrafterError
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class ErrorPage(ResponsePayload):
    """
    An ErrorPage is a payload that represents an error that occurred while
    processing a request. It contains a DrafterError object with details about
    the error.
    """

    error: DrafterError

    def render(
        self, state: SiteState, configuration: ClientServerConfiguration
    ) -> Optional[str]:
        content = [
            f"Message: {self.error.message}",
            f"Details: {self.error.details}",
            f"Where: {self.error.where}",
            f"Traceback: {self.error.traceback}",
        ]
        if self.error.traceback:
            content.append(f"Traceback:\n{self.error.traceback}")
        body = "\n".join(content)
        content = f"<div class='error-page'>\n"
        content += f"<pre>{body}</pre>\n"
        content += f"<div class='error-navigation'>"
        content += f"<a data-nav='index' class='error-home-link'>Return to Index Page</a>"
        content += f"<a data-nav='--reset' class='error-home-link'>Reset State and Return to Index</a>"
        content += "</div>\n"
        content += "</div>\n"
        site = "<form id='drafter-form--' enctype='multipart/form-data' accept-charset='utf-8'>"
        site += content
        site += "</form>"
        return site


@dataclass
class SimpleErrorPage(ResponsePayload):
    message: str

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        return f"Error: {self.message}"
