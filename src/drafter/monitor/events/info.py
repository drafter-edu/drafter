from dataclasses import dataclass
from typing import Any

from drafter.monitor.events.base import BaseEvent


@dataclass
class InfoEvent(BaseEvent):
    message: str = ""
    event_type: str = "Info"

    def to_json(self) -> dict[str, Any]:
        return {
            "message": self.message,
        }
