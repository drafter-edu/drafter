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
    def from_state(cls, state: Any, display: bool = True) -> "UpdatedStateEvent":
        """
        Builds an UpdatedStateEvent describing the given state value.

        Args:
            state: The state value to describe; it is recursively analyzed
                (to a maximum depth of 4) into a representation dict.
            display: Whether to describe the state at all (the
                `state_display` configuration setting). When False the
                state is not walked; the event carries a `hidden`
                representation naming only the state's type, which the
                debug panel shows as a one-line note.

        Returns:
            A new UpdatedStateEvent carrying the state's representation.
        """
        if not display:
            return cls(representation=hidden_representation(state))
        representation = analyze_type(state, max_depth=4)
        return cls(representation=representation)


def hidden_representation(state: Any) -> dict[str, Any]:
    """Describe a state whose display is turned off, without walking it.

    Args:
        state: The state value that is not being displayed.

    Returns:
        A representation dict of kind `hidden` with the fields every
        representation carries (`type`, `id`, `complexity`), so consumers
        can treat it like any other node.
    """
    return {
        "kind": "hidden",
        "type": type(state).__name__,
        "id": id(state),
        "complexity": 0,
    }
