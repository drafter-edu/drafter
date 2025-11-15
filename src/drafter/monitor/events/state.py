from dataclasses import dataclass
from typing import Any
import json

from drafter.monitor.events.base import BaseEvent
from drafter.history.utils import safe_repr


@dataclass
class UpdatedStateEvent(BaseEvent):
    html: str = ""
    event_type: str = "UpdatedState"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "html": self.html,
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "UpdatedStateEvent":
        html = f"<pre>{safe_repr(state)}</pre>"
        return cls(html=html)
