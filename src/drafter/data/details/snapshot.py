"""
State snapshot events for the debug panel's Save/Load feature.

A snapshot captures one route invocation (route + arguments) together with
the current state reduced to plain JSON data, so the debug UI can persist it
(browser localStorage or a downloaded file) and later restore it by
dispatching a ``drafter-load-state`` event back to the bridge, which
replays the route against the rebuilt state.
"""

from dataclasses import dataclass
from typing import Any

from drafter.data.details.recursive_type_describer import analyze_type
from drafter.data.telemetry import TelemetryRecord

#: Version stamp for the stored snapshot format (bumped on breaking changes).
SNAPSHOT_VERSION = 1


@dataclass
class StateSnapshotEvent(TelemetryRecord):
    """
    Event carrying a serialized snapshot of the state and current route.

    Published in response to the debug UI's ``drafter-save-state`` window
    event; the JS SaveLoadManager stores it (reason "save") or downloads it
    as a file (reason "download").

    Attributes:
        kind: Event-type discriminator, always "StateSnapshot"
        route: The route of the invocation being captured.
        kwargs_json: JSON-encoded keyword arguments of that invocation
            (empty dict when the arguments could not be serialized).
        state_json: The state as JSON-encoded plain data (dataclasses
            reduced to nested field dicts); rebuilt on load with the shared
            converter registry against the running app's state class.
        state_type: The state's class name at capture time (for labeling
            and mismatch diagnostics).
        representation: Recursive representation dict describing the state
            (for human-readable previews in slot pickers), see
            drafter.data.details.recursive_type_describer.
        reason: Why the snapshot was produced: "save" (store in a slot) or
            "download" (save as a file).
        slot: The storage slot the UI asked to save into (e.g. "quick",
            "slot-3"); meaningful only when reason is "save".
        app_title: The site title at capture time, for labeling slots.
        version: The snapshot format version (SNAPSHOT_VERSION).
    """

    kind: str = "StateSnapshot"
    route: str = "index"
    kwargs_json: str = "{}"
    state_json: str = ""
    state_type: str = ""
    representation: dict | None = None
    reason: str = "save"
    slot: str = "quick"
    app_title: str = ""
    version: int = SNAPSHOT_VERSION

    def to_json(self) -> dict[str, Any]:
        """
        Converts the StateSnapshotEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
            "route": self.route,
            "kwargs_json": self.kwargs_json,
            "state_json": self.state_json,
            "state_type": self.state_type,
            "representation": self.representation,
            "reason": self.reason,
            "slot": self.slot,
            "app_title": self.app_title,
            "version": self.version,
        }

    @classmethod
    def from_state(
        cls,
        state: Any,
        route: str,
        kwargs_json: str,
        reason: str,
        slot: str,
        app_title: str = "",
    ) -> "StateSnapshotEvent":
        """
        Builds a StateSnapshotEvent describing a captured state.

        Args:
            state: The state value being captured (used for the preview
                representation only; the JSON encoding happens in the
                bridge).
            route: The route of the captured invocation.
            kwargs_json: JSON-encoded arguments of the captured invocation.
            reason: "save" or "download".
            slot: The requested storage slot.
            app_title: The site title at capture time.

        Returns:
            A new StateSnapshotEvent without the state_json payload filled
            in (the bridge sets it after encoding).
        """
        representation = analyze_type(state, max_depth=4)
        return cls(
            route=route,
            kwargs_json=kwargs_json,
            representation=representation,
            reason=reason,
            slot=slot,
            app_title=app_title,
        )
