"""
State update events carrying recursive descriptions of the server's state
for the debug UI.
"""

from dataclasses import dataclass
from typing import Any

from drafter.data.details.recursive_type_describer import analyze_type
from drafter.data.telemetry import TelemetryRecord


@dataclass
class UpdatedStateEvent(TelemetryRecord):
    """
    Event emitted when the server's state changes.

    Attributes:
        kind: Event-type discriminator, always "UpdatedState"
        representation: Recursive representation dict describing the new
            state (see drafter.data.details.recursive_type_describer)
    """

    kind: str = "UpdatedState"
    representation: dict | None = None

    def to_json(self) -> dict[str, Any]:
        """
        Converts the UpdatedStateEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
            "representation": self.representation,
        }

    @classmethod
    def from_state(cls, state: Any) -> "UpdatedStateEvent":
        """
        Builds an UpdatedStateEvent describing the given state value.

        Args:
            state: The state value to describe; it is recursively analyzed
                (to a maximum depth of 4) into a representation dict.

        Returns:
            A new UpdatedStateEvent carrying the state's representation.
        """
        representation = analyze_type(state, max_depth=4)
        return cls(representation=representation)
