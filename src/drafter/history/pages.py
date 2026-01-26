"""
Page visit tracking for debugging and history purposes.
"""

import html
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from typing import Any, Optional, Callable


@dataclass
class VisitedPage:
    """
    Records information about a page visit during request processing.

    Attributes:
        url: The URL of the page being visited
        function: The route function being called
        arguments: String representation of the function arguments
        status: Current status of the page processing
        button_pressed: The button namespace if a button was pressed
        original_page_content: The original page content for debugging
        old_state: The state before the page was processed
        started: Timestamp when processing started
        stopped: Timestamp when processing finished (None if still processing)
    """

    url: str
    function: Callable
    arguments: str
    status: str
    button_pressed: str = ""
    original_page_content: Optional[str] = None
    old_state: Any = None
    started: datetime = dataclass_field(default_factory=lambda: datetime.now())
    stopped: Optional[datetime] = None

    def update(self, new_status, original_page_content=None):
        """
        Updates the status and optionally the page content.

        Args:
            new_status: The new status string
            original_page_content: Optional page content to store
        """
        self.status = new_status
        if original_page_content is not None:
            # Store the page content (simplified - no special formatting)
            content = html.escape(repr(original_page_content))
            self.original_page_content = content

    def finish(self, new_status):
        """
        Marks the page processing as finished.

        Args:
            new_status: The final status string
        """
        self.status = new_status
        self.stopped = datetime.now()

    def as_html(self):
        """
        Returns an HTML representation of the visited page.

        Returns:
            HTML string
        """
        function_name = self.function.__name__
        return (
            f"<strong>Current Route:</strong><br>Route function: <code>{function_name}</code><br>"
            f"URL: <href='{self.url}'><code>{self.url}</code></href>"
        )
