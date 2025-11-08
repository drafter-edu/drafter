from typing import Optional
from dataclasses import dataclass
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.errors import DrafterError
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
        content = f"<div class='error-page'>\n<pre>{body}</pre>\n</div>"
        site = "<form id='drafter-form--' enctype='multipart/form-data' accept-charset='utf-8'>"
        site += content
        site += "</form>"
        return site


@dataclass
class SimpleErrorPage(ResponsePayload):
    message: str

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        return f"Error: {self.message}"
