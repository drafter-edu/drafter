"""Geolocation components for requesting and displaying location data.

Provides the CurrentLocation component and Location dataclass for handling
browser geolocation API integration with form-based workflows.

The Python side only describes the component: it renders as a
``<drafter-current-location>`` custom element whose behavior (permission
workflow, status UI, form value updates) is implemented in
js/src/components/geolocation.tsx. The element keeps a hidden form field
named after the component updated with JSON-encoded location data;
:func:`convert_location` (registered below into the shared converter
registry) turns that payload into a :class:`Location` when the matching
route parameter is annotated with it.
"""

import json
from dataclasses import dataclass
from typing import Optional, Literal

from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction
from drafter.components.utilities.contracts import (
    ComponentContract,
    EventPayloadFieldSpec,
    EventPayloadSpec,
)
from drafter.components.utilities.registry import (
    COMPONENT_CONTRACT_REGISTRY,
    CONVERTER_REGISTRY,
)
from drafter.components.utilities.validation import validate_parameter_name
from drafter.data.converter import ConversionContext, ConversionResult


LocationStatus = Literal[
    "unavailable", "prompt", "granted", "denied", "pending", "error"
]


@dataclass
class Location:
    """Geolocation data from the browser's geolocation API.

    Attributes:
        status: Current permission/availability state.
        message: Optional descriptive message about the status.
        latitude: Latitude in decimal degrees (None if unavailable).
        longitude: Longitude in decimal degrees (None if unavailable).
        accuracy: Position accuracy in meters (None if unavailable).
        altitude: Altitude in meters above sea level (None if unavailable).
        heading: Direction of travel in degrees (None if unavailable).
        speed: Speed in meters per second (None if unavailable).
        timestamp: Unix timestamp of position acquisition (None if unavailable).
    """

    status: LocationStatus
    message: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    timestamp: Optional[float] = None


def _is_location_type(target) -> bool:
    return target is Location


def convert_location(ctx: ConversionContext) -> Optional[ConversionResult]:
    """Convert a JSON string or dict payload into a :class:`Location`."""
    value = ctx.raw_value
    if isinstance(value, Location):
        return ConversionResult(ok=True, value=value)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            # An unparseable location is a status, not a crash: routes can
            # inspect the error without students needing try/except.
            return ConversionResult(
                ok=True,
                value=Location(
                    status="error",
                    message=f"Failed to parse location data: {error}",
                ),
            )
    if isinstance(value, dict):
        try:
            return ConversionResult(ok=True, value=Location(**value))
        except TypeError as error:
            return ConversionResult(
                ok=True,
                value=Location(
                    status="error",
                    message=f"Failed to parse location data: {error}",
                ),
            )
    return None


CONVERTER_REGISTRY.register_predicate(
    _is_location_type, convert_location, priority=20, name="Location"
)


@dataclass(repr=False)
class CurrentLocation(Component):
    """A form component that requests and displays browser geolocation.

    This component integrates with the browser's Geolocation API to request
    user permission and provide location data. It handles multiple visual
    states based on permission status and keeps a hidden form field (named
    ``name``) updated with the JSON-encoded location, so a route parameter
    with the same name annotated as :class:`Location` receives the converted
    value.

    Visual states:
    - prompt: Shows "Use my location" button when permission not yet requested
    - pending: Shows spinner while waiting for permission
    - denied: Shows "Location access denied" message with help
    - granted: Shows "Location available" with optional coordinates
    - error: Shows error message if geolocation fails
    - unavailable: Shows message if geolocation API not supported

    Attributes:
        name: The form field name that will contain location data.
        show: Whether to display the geolocation status UI. Defaults to True.
        show_coordinates: Whether to display latitude/longitude when granted (default: False).
        on_locate: Function or URL to call when a location (or failure) is
            resolved. Defaults to None.
    """

    name: str
    show: bool = True
    show_coordinates: bool = False
    on_locate: Optional[UrlOrFunction] = None

    tag = "drafter-current-location"

    KNOWN_ATTRS = ["name", "show", "show-coordinates"]
    ARGUMENTS = [
        ComponentArgument("name", "positional"),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("show_coordinates", "keyword", False),
        ComponentArgument("on_locate", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["locate"]

    #: What this component emits: the JS implementation (js/src/components/
    #: geolocation.tsx) must match this contract, and the router uses it to
    #: reason about event payload fields.
    CONTRACT = ComponentContract(
        component_name="CurrentLocation",
        html_tag="drafter-current-location",
        emitted_events=[
            EventPayloadSpec(
                event_name="locate",
                fields=[
                    EventPayloadFieldSpec(
                        "status",
                        str,
                        "Permission/availability state: granted, denied, or error.",
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the status."
                    ),
                    EventPayloadFieldSpec(
                        "latitude", float, "Latitude in decimal degrees."
                    ),
                    EventPayloadFieldSpec(
                        "longitude", float, "Longitude in decimal degrees."
                    ),
                    EventPayloadFieldSpec(
                        "accuracy", float, "Position accuracy in meters."
                    ),
                    EventPayloadFieldSpec(
                        "altitude", float, "Altitude in meters above sea level."
                    ),
                    EventPayloadFieldSpec(
                        "heading", float, "Direction of travel in degrees."
                    ),
                    EventPayloadFieldSpec(
                        "speed", float, "Speed in meters per second."
                    ),
                    EventPayloadFieldSpec(
                        "timestamp", float, "Unix timestamp of position acquisition."
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        name: str,
        show: bool = True,
        show_coordinates: bool = False,
        on_locate: Optional[UrlOrFunction] = None,
        **extra_settings,
    ):
        """Initialize the CurrentLocation component.

        Args:
            name: The form field name for geolocation data.
            show: Whether to display the geolocation status UI.
            show_coordinates: Whether to display coordinates when available.
            on_locate: Function or URL to call when a location is resolved.
            **extra_settings: Additional HTML attributes.
        """
        validate_parameter_name(name, "CurrentLocation")
        self.name = name
        self.show = show
        self.show_coordinates = show_coordinates
        self.on_locate = on_locate
        self.extra_settings = extra_settings


COMPONENT_CONTRACT_REGISTRY.register(CurrentLocation.CONTRACT)
