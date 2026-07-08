from dataclasses import dataclass
from typing import Any, Literal, Optional


PayloadSource = Literal[
    #: Custom component `args`
    "component_argument",  # data--drafter-arguments
    "event_detail",  # CustomEvent.detail
    "form_field",  # form inputs
    "framework_meta",  # request metadata injected by framework
]

#: Student-facing phrases for each payload source, used in diagnostics.
SOURCE_PHRASES: dict[str, str] = {
    "component_argument": "the component argument",
    "event_detail": "the event value",
    "form_field": "the form field",
    "framework_meta": "the framework value",
}


@dataclass
class PayloadValue:
    name: str
    value: Any
    source: PayloadSource
    source_detail: str = ""  # e.g., component tag/id, field name, event name


def describe_source(value: Optional[PayloadValue], fallback_name: str = "") -> str:
    """Student-facing description of where a payload value came from,
    e.g. ``"the form field 'age'"``."""
    if value is None:
        if fallback_name:
            return f"the value for '{fallback_name}'"
        return "the request"
    phrase = SOURCE_PHRASES.get(value.source, "the value")
    detail = f" ({value.source_detail})" if value.source_detail else ""
    return f"{phrase} '{value.name}'{detail}"
