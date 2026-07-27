"""
Collect and normalize stages of the parameter pipeline.

Collect builds one request payload — with per-key source provenance — from
the event detail, component argument payloads, form fields, and framework
metadata. Normalize applies component-declared aliases so the binder only
ever sees canonical names.
"""

from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.data.payload import PayloadValue
from drafter.data.request import Request

#: Sources the bridge is allowed to claim; anything else demotes to form_field.
_VALID_SOURCES = {"component_argument", "event_detail", "form_field", "framework_meta"}


def collect_payload(request: Request, button_pressed: str = "") -> list[PayloadValue]:
    """Build the provenance-tagged payload for a request.

    Prefers the structured ``request.raw_payload`` entries produced by the
    bridge (which carry per-key sources); falls back to treating the merged
    ``request.kwargs`` as form fields for older clients, redirects, and
    history navigation.

    Args:
        request: The incoming request.
        button_pressed: The extracted submit-button namespace, exposed as
            optional framework metadata (bindable by a ``button_pressed``
            parameter, never warned about when unused).
    """
    entries: list[PayloadValue] = []
    if request.raw_payload:
        for raw in request.raw_payload:
            name = str(raw.get("name", ""))
            if not name or name == SUBMIT_BUTTON_KEY:
                continue
            source = raw.get("source", "form_field")
            if source not in _VALID_SOURCES:
                source = "form_field"
            entries.append(
                PayloadValue(
                    name=name,
                    value=raw.get("value"),
                    source=source,
                    source_detail=str(raw.get("source_detail", "") or ""),
                )
            )
    else:
        for key, value in request.kwargs.items():
            key = str(key)
            if key == SUBMIT_BUTTON_KEY:
                continue
            entries.append(
                PayloadValue(
                    name=key,
                    value=value,
                    source="form_field",
                    source_detail=request.action,
                )
            )
    if button_pressed and isinstance(button_pressed, str):
        entries.append(
            PayloadValue(
                name="button_pressed",
                value=button_pressed,
                source="framework_meta",
                source_detail="request metadata",
            )
        )
    return entries


def normalize_payload(
    entries: list[PayloadValue], alias_map: dict[str, str]
) -> list[PayloadValue]:
    """Rename aliased payload keys to their canonical names.

    The alias map is aggregated from component contracts
    (see ``ComponentContractRegistry.alias_map``).
    """
    if not alias_map:
        return list(entries)
    normalized: list[PayloadValue] = []
    for entry in entries:
        canonical = alias_map.get(entry.name)
        if canonical and canonical != entry.name:
            detail = entry.source_detail or ""
            alias_note = f"as '{entry.name}'"
            detail = f"{detail}, {alias_note}" if detail else alias_note
            normalized.append(
                PayloadValue(
                    name=canonical,
                    value=entry.value,
                    source=entry.source,
                    source_detail=detail,
                )
            )
        else:
            normalized.append(entry)
    return normalized
