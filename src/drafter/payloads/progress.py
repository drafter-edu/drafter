"""
Progress payload for streaming responses and progress updates.

This module provides the Progress class which represents progress updates
for long-running operations or streaming responses.
"""

from dataclasses import dataclass
from typing import Optional
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Progress(ResponsePayload):
    """
    Represents a progress update for a long-running operation.

    Progress payloads can be yielded from route handlers to provide incremental
    updates to the user during long-running tasks. They can show progress bars,
    status messages, or partial results.

    :ivar message: A status message describing the current progress.
    :ivar percentage: Optional percentage completion (0-100).
    :ivar current: Optional current step number.
    :ivar total: Optional total number of steps.
    """

    message: str
    percentage: Optional[float] = None
    current: Optional[int] = None
    total: Optional[int] = None

    def render(self, state: SiteState, configuration: ClientServerConfiguration) -> str:
        """
        Renders the progress update.

        :param state: The current state of the site.
        :param configuration: The client server configuration.
        :return: HTML content showing the progress.
        """
        content = [f"<div class='drafter-progress'>"]
        content.append(f"<p>{self.message}</p>")
        
        if self.percentage is not None:
            content.append(f"<progress value='{self.percentage}' max='100'></progress>")
            content.append(f"<span>{self.percentage:.1f}%</span>")
        elif self.current is not None and self.total is not None:
            percentage = (self.current / self.total) * 100
            content.append(f"<progress value='{self.current}' max='{self.total}'></progress>")
            content.append(f"<span>{self.current} / {self.total}</span>")
        
        content.append("</div>")
        return "\n".join(content)
