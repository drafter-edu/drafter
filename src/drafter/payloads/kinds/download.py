from typing import Optional, Union
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure
from drafter.data.request import Request
from drafter.router.routes import Router


@dataclass
class Download(ResponsePayload):
    """
    A Download is a payload that will trigger a file download in the browser.
    
    :param file_name: The name of the file to be downloaded.
    :param content: The file content, either as bytes or a string.
    :param mime_type: The MIME type of the file (default: "application/octet-stream").
    """

    file_name: str
    content: Union[bytes, str]
    mime_type: str = "application/octet-stream"
    
    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> Optional[str]:
        # Downloads don't render HTML content
        return None
    
    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        if not isinstance(self.file_name, str):
            return VerificationFailure(
                f"Download payload from {request.url} must have file_name as a string. "
                f"Found {type(self.file_name).__name__} instead."
            )
        
        if not isinstance(self.content, (bytes, str)):
            return VerificationFailure(
                f"Download payload from {request.url} must have content as bytes or string. "
                f"Found {type(self.content).__name__} instead."
            )
        
        if not isinstance(self.mime_type, str):
            return VerificationFailure(
                f"Download payload from {request.url} must have mime_type as a string. "
                f"Found {type(self.mime_type).__name__} instead."
            )
        
        return None
