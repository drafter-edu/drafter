"""
Configuration and server information events.
"""

from dataclasses import dataclass
from typing import Any

from drafter.monitor.events.base import BaseEvent


@dataclass
class ConfigurationEvent(BaseEvent):
    """
    Event emitted when configuration information needs to be displayed.

    :ivar backend: Backend type (e.g., 'starlette', 'skulpt')
    :ivar host: Server host
    :ivar port: Server port
    :ivar title: Site title
    :ivar framed: Whether site is framed
    :ivar style: Style configuration
    :ivar in_debug_mode: Whether debug mode is enabled
    """

    backend: str = ""
    host: str = ""
    port: int = 0
    title: str = ""
    framed: bool = True
    style: str = ""
    in_debug_mode: bool = True
    event_type: str = "ConfigurationEvent"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "backend": self.backend,
            "host": self.host,
            "port": self.port,
            "title": self.title,
            "framed": self.framed,
            "style": self.style,
            "in_debug_mode": self.in_debug_mode,
        }
