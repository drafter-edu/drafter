"""Dataclasses describing the Python-JS component contract.

Each interactive component declares a `ComponentContract`: the custom
element tag it renders as, the events it emits (as `EventPayloadSpec`
entries built from `EventPayloadFieldSpec` fields), any synthetic payload
fields it contributes beyond form inputs, and the helper callables
(`HelperSpec`, built from a `HelperContext`) it offers to routes handling
its events. The JS implementation of each component must match its
declared contract; the sibling `registry` module aggregates all contracts
at startup so the router can reason globally about binding, aliases, and
helper injection.

This module is a leaf: it defines only the contract structures, with no
browser or router imports.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventPayloadFieldSpec:
    """One field a component event contributes to the request payload.

    Attributes:
        name: Canonical payload key routes can declare as a parameter.
        python_type: The Python type the value arrives as after the
            bridge decodes the event detail.
        documentation: Student-facing description of the field, used in
            docs generation and diagnostics.
    """

    name: str
    python_type: type
    documentation: str


@dataclass
class EventPayloadSpec:
    """The payload one component event promises to deliver.

    Attributes:
        event_name: The event that fires (matched against a Request's
            `action`).
        fields: Fields always present in the event's payload.
        optional_fields: Fields the event may include but does not
            guarantee.
        aliases: Mapping of canonical field name to a list of alternate
            payload names, e.g. `{"latitude": ["lat"]}`. The contract
            registry's `alias_map` flattens these into an
            alternate-to-canonical mapping so the router's normalize
            stage rewrites incoming keys to canonical names before
            binding.
    """

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
    """Everything a component declares about its runtime behavior.

    The Python side defines the contract, the JS implementation of the
    component must match it, and the contract registry aggregates all
    contracts at startup so the router can reason globally (payload
    binding, alias normalization, helper injection, docs generation).

    Attributes:
        component_name: The Python class name of the component
            (e.g., "Map").
        html_tag: The custom element tag the component renders as
            (lowercase, e.g., "drafter-map"); used to match DOM events
            back to the contract.
        emitted_events: One `EventPayloadSpec` per event the component
            emits, describing the payload each delivers.
        synthetic_fields: Extra non-form payload field names the
            component contributes (beyond regular form inputs).
        provided_helpers: `HelperSpec` callables injected into routes
            that handle this component's events.
    """

    component_name: str
    html_tag: str
    emitted_events: list[EventPayloadSpec]
    synthetic_fields: list[str] = field(default_factory=list)
    provided_helpers: list[HelperSpec] = field(default_factory=list)
