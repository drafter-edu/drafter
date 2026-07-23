"""
Provenance-tagged request payload values: each value the client sends is
tagged with where it came from, so that diagnostics can tell students
exactly which form field, event, or component argument produced it.
"""

from dataclasses import dataclass
from typing import Any, Literal

PayloadSource = Literal[
    #: Custom component `args`
    "component_argument",  # data--drafter-arguments
    "event_detail",  # CustomEvent.detail
    "form_field",  # form inputs
    "framework_meta",  # request metadata injected by framework
]
"""The provenance of a payload value: a custom component argument, a
CustomEvent detail, a form input, or framework-injected request metadata."""

SOURCE_PHRASES: dict[str, str] = {
    "component_argument": "the component argument",
    "event_detail": "the event value",
    "form_field": "the form field",
    "framework_meta": "the framework value",
}
"""Student-facing phrases for each payload source, used in diagnostics."""


@dataclass
class PayloadValue:
    """One request value tagged with its provenance.

    Attributes:
        name: The parameter name the value is bound to.
        value: The raw value sent by the client.
        source: Where the value came from (one of the PayloadSource options).
        source_detail: Extra provenance detail, such as the component
            tag/id, field name, or event name.
    """

    name: str
    value: Any
    source: PayloadSource
    source_detail: str = ""  # e.g., component tag/id, field name, event name


def describe_source(value: PayloadValue | None, fallback_name: str = "") -> str:
    """Student-facing description of where a payload value came from,
    e.g. ``"the form field 'age'"``.

    Args:
        value: The payload value to describe, or None if the value's
            provenance is unknown. Its `source` selects a phrase from
            `SOURCE_PHRASES` (falling back to "the value"), and its
            `source_detail`, when present, is appended in parentheses.
        fallback_name: Name used when `value` is None; produces
            ``"the value for '<fallback_name>'"``. If empty as well, the
            generic ``"the request"`` is returned.

    Returns:
        Human-readable phrase such as ``"the form field 'age'"`` or
        ``"the event value 'latitude' (drafter-map)"``, suitable for
        student-facing diagnostics.
    """
    if value is None:
        if fallback_name:
            return f"the value for '{fallback_name}'"
        return "the request"
    phrase = SOURCE_PHRASES.get(value.source, "the value")
    detail = f" ({value.source_detail})" if value.source_detail else ""
    return f"{phrase} '{value.name}'{detail}"
