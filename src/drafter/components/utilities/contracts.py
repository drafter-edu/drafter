from dataclasses import dataclass, field
from typing import Any, Callable


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
class HelperContext:
    """What a helper factory gets to work with when a component event fires.

    Attributes:
        element: The live DOM element that emitted the event. Helpers may
            call standard element methods (getAttribute, setAttribute) on it;
            the object itself comes from the bridge, so this module stays
            free of browser imports.
        values: The merged request values (event detail and form fields).
    """

    element: Any
    values: dict


@dataclass
class HelperSpec:
    """A callable a component offers to routes handling its events.

    When a route triggered by one of the component's events declares a
    parameter with this name, the router injects ``factory(context)``'s
    return value (see ``extra_dependencies`` in the binder). Helpers bind
    before request data and are never taken from the payload.

    Attributes:
        name: The route parameter name that receives the helper.
        factory: Builds the injected value from a :class:`HelperContext`.
        documentation: Student-facing description of what the helper does.
        events: Event names that provide this helper; empty means every
            event the component emits.
    """

    name: str
    factory: Callable[[HelperContext], Any]
    documentation: str = ""
    events: tuple = ()


@dataclass
class ComponentContract:
    component_name: str
    html_tag: str
    emitted_events: list[EventPayloadSpec]
    #: extra non-form fields it contributes
    synthetic_fields: list[str] = field(default_factory=list)
    #: callables injected into routes handling this component's events
    provided_helpers: list[HelperSpec] = field(default_factory=list)
