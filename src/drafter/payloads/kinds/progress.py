from typing import Optional
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure
from drafter.data.request import Request
from drafter.router.routes import Router


@dataclass
class Progress(ResponsePayload):
    """
    A Progress is a payload that can be sent to indicate progress on a long-running
    task. This allows streaming partial results to the client.
    
    :param message: A message describing the current progress.
    :param percent: Optional percentage complete (0-100).
    :param html: Optional HTML content to display with the progress update.
    """
    
    message: str
    percent: Optional[float] = None
    html: Optional[str] = None
    
    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> Optional[str]:
        # If HTML is provided, use it; otherwise create basic progress display
        if self.html:
            return self.html
        
        progress_html = f'<div class="progress-update">'
        progress_html += f'<p>{self.message}</p>'
        if self.percent is not None:
            progress_html += f'<progress value="{self.percent}" max="100"></progress>'
            progress_html += f'<span>{self.percent:.1f}%</span>'
        progress_html += '</div>'
        return progress_html
    
    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        if not isinstance(self.message, str):
            return VerificationFailure(
                f"Progress payload from {request.url} must have message as a string. "
                f"Found {type(self.message).__name__} instead."
            )
        
        if self.percent is not None:
            if not isinstance(self.percent, (int, float)):
                return VerificationFailure(
                    f"Progress payload from {request.url} must have percent as a number or None. "
                    f"Found {type(self.percent).__name__} instead."
                )
            if self.percent < 0 or self.percent > 100:
                return VerificationFailure(
                    f"Progress payload from {request.url} must have percent between 0 and 100. "
                    f"Found {self.percent} instead."
                )
        
        if self.html is not None and not isinstance(self.html, str):
            return VerificationFailure(
                f"Progress payload from {request.url} must have html as a string or None. "
                f"Found {type(self.html).__name__} instead."
            )
        
        return None
