from dataclasses import dataclass
from typing import Any, Optional

from drafter.data.telemetry import TelemetryRecord
from drafter.data.details.recursive_type_describer import analyze_type


@dataclass
class UpdatedStateEvent(TelemetryRecord):
    kind: str = "UpdatedState"
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
