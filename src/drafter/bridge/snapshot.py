"""
State snapshot serialization for the bridge's Save/Load feature.

A snapshot stores the route invocation (route + kwargs) and the state as
plain JSON data (dataclasses become field dicts via ``dataclasses.asdict``).
Loading rebuilds the state with the same converter registry the router uses
for route parameters, targeting the running app's state class — no pickle,
so snapshots survive code edits/restarts as long as the state's shape still
matches.
"""

import dataclasses
import json
from typing import Any

from drafter.bridge.error_handling import report_bridge_error, report_bridge_warning
from drafter.data.converter import ConversionContext
from drafter.data.details.snapshot import StateSnapshotEvent

# Importing the router's conversion module installs the shared converters
# (dataclasses, scalars, collections, ...) into CONVERTER_REGISTRY.
from drafter.router.parameters.conversion import CONVERTER_REGISTRY

# Marker key for circular references in encoded snapshots. The value is the
# path (list of field names / indices / keys) from the snapshot root to the
# object being referenced. Cannot collide with dataclass field names because
# it is not a valid Python identifier.
REFERENCE_KEY = "$drafter_ref"


def encode_state_value(state: Any) -> Any:
    """Reduce a state value to plain JSON-ready data.

    Dataclass instances become nested field dicts; primitives, lists, and
    dicts pass through unchanged. Circular references are encoded as
    ``{"$drafter_ref": <path-to-ancestor>}`` markers instead of recursing
    forever, so cyclic states (linked lists, trees with parent pointers,
    graphs) can be saved and restored.
    """
    return _encode_value(state, [], {})


def _encode_value(value: Any, path: list, active: dict[int, list]) -> Any:
    """Recursively encode a value, replacing cycles with reference markers.

    Args:
        value: The value being encoded.
        path: The path from the snapshot root to this value.
        active: Maps id() of each container on the current ancestor chain to
            its path; a revisit means a cycle.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        marker = active.get(id(value))
        if marker is not None:
            return {REFERENCE_KEY: marker}
        active[id(value)] = path
        try:
            return {
                field.name: _encode_value(
                    getattr(value, field.name), path + [field.name], active
                )
                for field in dataclasses.fields(value)
            }
        finally:
            del active[id(value)]
    if isinstance(value, (list, tuple)):
        marker = active.get(id(value))
        if marker is not None:
            return {REFERENCE_KEY: marker}
        active[id(value)] = path
        try:
            return [
                _encode_value(item, path + [index], active)
                for index, item in enumerate(value)
            ]
        finally:
            del active[id(value)]
    if isinstance(value, dict):
        marker = active.get(id(value))
        if marker is not None:
            return {REFERENCE_KEY: marker}
        active[id(value)] = path
        try:
            return {
                key: _encode_value(item, path + [key], active)
                for key, item in value.items()
            }
        finally:
            del active[id(value)]
    return value


def _strip_reference_markers(value: Any, path: list, patches: list) -> Any:
    """Replace ``$drafter_ref`` markers with None, recording patch locations.

    Returns the cleaned value. Each recorded patch is a
    ``(marker_path, target_path)`` pair to be re-linked after the state has
    been rebuilt.
    """
    if isinstance(value, dict):
        if set(value.keys()) == {REFERENCE_KEY}:
            patches.append((path, value[REFERENCE_KEY]))
            return None
        return {
            key: _strip_reference_markers(item, path + [key], patches)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _strip_reference_markers(item, path + [index], patches)
            for index, item in enumerate(value)
        ]
    return value


def _resolve_path(root: Any, path: list) -> Any:
    """Walk a path of field names / indices / keys from a rebuilt state."""
    value = root
    for step in path:
        if isinstance(value, (list, tuple)):
            value = value[int(step)]
        elif isinstance(value, dict):
            if step not in value and isinstance(step, str):
                # JSON stringifies keys; tolerate int keys after conversion.
                try:
                    value = value[int(step)]
                    continue
                except (KeyError, ValueError):
                    pass
            value = value[step]
        else:
            value = getattr(value, str(step))
    return value


def _apply_reference_patches(root: Any, patches: list) -> None:
    """Re-link circular references stripped out of a decoded snapshot."""
    for marker_path, target_path in patches:
        target = _resolve_path(root, target_path)
        if not marker_path:
            continue
        parent = _resolve_path(root, marker_path[:-1])
        last = marker_path[-1]
        if isinstance(parent, list):
            parent[int(last)] = target
        elif isinstance(parent, dict):
            parent[last] = target
        else:
            setattr(parent, str(last), target)


def serialize_state_snapshot(
    state: Any,
    route: str,
    kwargs: dict,
    reason: str,
    slot: str,
    app_title: str = "",
) -> StateSnapshotEvent | None:
    """Capture the given state and route invocation as a snapshot event.

    Args:
        state: The current state value, stored as plain JSON data.
        route: The route of the invocation being captured.
        kwargs: The keyword arguments of that invocation; serialized to
            JSON with the same empty-dict fallback the browser history uses.
        reason: "save" (store in a slot) or "download" (save as a file).
        slot: The storage slot the UI asked to save into.
        app_title: The site title at capture time.

    Returns:
        The StateSnapshotEvent to publish, or None when the state could not
        be reduced to simple data (an error is reported instead).
    """
    try:
        state_json = json.dumps(encode_state_value(state))
    except Exception as e:
        report_bridge_error(
            "bridge.snapshot_encode_failed",
            "Could not save the state: it contains something that cannot be "
            "stored as simple data",
            "bridge.snapshot.serialize_state_snapshot",
            f"State: {repr(state)[:500]}",
            exception=e,
            route=route,
            phase="event_dispatch",
        )
        return None
    try:
        kwargs_json = json.dumps(kwargs) if kwargs else "{}"
    except Exception as e:
        report_bridge_warning(
            "bridge.snapshot_kwargs_serialization_failed",
            "Could not serialize the route arguments for the snapshot; using empty arguments",
            "bridge.snapshot.serialize_state_snapshot",
            f"Request kwargs: {repr(kwargs)}",
            exception=e,
            route=route,
            phase="event_dispatch",
        )
        kwargs_json = "{}"
    event = StateSnapshotEvent.from_state(
        state, route, kwargs_json, reason, slot, app_title
    )
    event.state_json = state_json
    event.state_type = type(state).__name__
    return event


def deserialize_state_snapshot(state_json: str, current_state: Any) -> Any:
    """Rebuild a saved state value for the running application.

    The stored JSON data is converted back to the class of the app's
    *current* state via the shared converter registry (the same machinery
    that builds dataclasses from route parameters), so nested dataclass
    fields are reconstructed by name using the live class definitions.

    Args:
        state_json: The snapshot's JSON-encoded state data.
        current_state: The app's current state value; its type is the
            reconstruction target. When it is None (no state recorded yet),
            the decoded data is returned as-is.

    Returns:
        The restored state value.

    Raises:
        ValueError: When the data no longer matches the running state
            class (e.g. the code changed shape since the save).
        Exception: Whatever ``json.loads`` raises for corrupt payloads.
    """
    raw = json.loads(state_json)
    patches: list = []
    raw = _strip_reference_markers(raw, [], patches)
    if current_state is None:
        _apply_reference_patches(raw, patches)
        return raw
    target = type(current_state)
    result = CONVERTER_REGISTRY.convert(
        ConversionContext(
            param_name="state",
            expected_type=target,
            raw_value=raw,
            route_name="--load-state",
        )
    )
    if not result.ok:
        raise ValueError(
            f"The saved state no longer matches this application's "
            f"{target.__name__} state: {result.message} {result.hint}".strip()
        )
    _apply_reference_patches(result.value, patches)
    return result.value
