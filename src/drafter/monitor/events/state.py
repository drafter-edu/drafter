from dataclasses import dataclass
from typing import Any, Optional

from drafter.monitor.events.base import BaseEvent
from drafter.history.utils import safe_repr
from drafter.monitor.events.recursive_type_describer import analyze_type


@dataclass
class UpdatedStateEvent(BaseEvent):
    event_type: str = "UpdatedState"
    representation: Optional[dict] = None

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "representation": self.representation,
        }

    @classmethod
    def from_state(cls, state: Any) -> "UpdatedStateEvent":
        representation = analyze_type(state, max_depth=4)
        return cls(representation=representation)