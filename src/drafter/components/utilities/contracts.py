from dataclasses import dataclass, field


@dataclass
class EventPayloadFieldSpec:
    name: str
    python_type: type
    documentation: str


@dataclass
class EventPayloadSpec:
    event_name: str
    fields: list[EventPayloadFieldSpec]
    optional_fields: list[EventPayloadFieldSpec] = field(default_factory=list)
    aliases: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ComponentContract:
    component_name: str
    html_tag: str
    emitted_events: list[EventPayloadSpec]
    #: extra non-form fields it contributes
    synthetic_fields: list[str] = field(default_factory=list)
