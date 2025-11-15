from dataclasses import dataclass
from typing import Any
import json

from drafter.monitor.events.base import BaseEvent


@dataclass
class RouteAddedEvent(BaseEvent):
    url: str = ""
    signature: str = ""
    event_type: str = "RouteAdded"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "url": self.url,
            "signature": self.signature,
        }
