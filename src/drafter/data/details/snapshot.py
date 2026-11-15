"""
State snapshot events for the debug panel's Save/Load feature.

A snapshot captures one route invocation (route + arguments) together with
the state reduced to plain JSON data, both as it is now and as it was just
before that route ran, so the debug UI can persist it (browser localStorage
or a downloaded file) and later restore it by dispatching a
``drafter-load-state`` event back to the bridge, which puts the earlier
state back and runs the route again.
"""

from dataclasses import dataclass
from typing import Any

from drafter.data.details.recursive_type_describer import analyze_type
from drafter.data.telemetry import TelemetryRecord

SNAPSHOT_VERSION = 2
"""Version stamp for the stored snapshot format.

Version 1 stored only the state from after the route ran. Version 2 adds
`state_before_json`, the state from before the route ran; loading restores
that one, so that running the route again arrives at the saved page instead
of one step past it. A snapshot without `state_before_json` (version 1, or
a version 2 save whose earlier state could not be captured) is loaded the
version 1 way."""


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
            converter registry against the running app's state class. This
            is the state as it is now, after the captured route ran.
        state_before_json: The state as it was just before the captured
            route ran, encoded the same way, or "" when it is not known.
            Loading restores this state and runs the route again, which
            reproduces the saved page (the way the browser's Back button
            restores an entry).
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
    state_before_json: str = ""
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
            "state_before_json": self.state_before_json,
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
            A new StateSnapshotEvent without the state_json and
            state_before_json payloads filled in (the bridge sets them
            after encoding).
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
