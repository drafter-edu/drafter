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
from typing import Literal

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
"""The permission/availability states a `Location`'s `status` field can
report, mirroring the browser geolocation permission workflow."""


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
    message: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    accuracy: float | None = None
    altitude: float | None = None
    heading: float | None = None
    speed: float | None = None
    timestamp: float | None = None


def _is_location_type(target) -> bool:
    return target is Location


def convert_location(ctx: ConversionContext) -> ConversionResult | None:
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
        enable_high_accuracy: Whether to prefer high-accuracy geolocation. Defaults to True.
        timeout: Maximum time to wait for a position in milliseconds. Defaults to 10000.
        maximum_age: Maximum cached position age in milliseconds. Defaults to 0.
        on_locate: Function or URL to call when a location (or failure) is
            resolved. Defaults to None.
        on_error: Function or URL to call when geolocation fails for any reason.
        on_denied: Function or URL to call when geolocation permission is denied.
        on_timeout: Function or URL to call when geolocation request times out.
    """

    name: str
    show: bool = True
    show_coordinates: bool = False
    enable_high_accuracy: bool = True
    timeout: int = 10000
    maximum_age: int = 0
    on_locate: UrlOrFunction | None = None
    on_error: UrlOrFunction | None = None
    on_denied: UrlOrFunction | None = None
    on_timeout: UrlOrFunction | None = None

    tag = "drafter-current-location"

    KNOWN_ATTRS = [
        "name",
        "show",
        "show-coordinates",
        "enable-high-accuracy",
        "timeout",
        "maximum-age",
    ]
    ARGUMENTS = [
        ComponentArgument("name", "positional"),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("show_coordinates", "keyword", False),
        ComponentArgument("enable_high_accuracy", "keyword", True),
        ComponentArgument("timeout", "keyword", 10000),
        ComponentArgument("maximum_age", "keyword", 0),
        ComponentArgument("on_locate", "keyword", None, is_event=True),
        ComponentArgument("on_error", "keyword", None, is_event=True),
        ComponentArgument("on_denied", "keyword", None, is_event=True),
        ComponentArgument("on_timeout", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["locate", "error", "denied", "timeout"]

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
            EventPayloadSpec(
                event_name="error",
                fields=[
                    EventPayloadFieldSpec(
                        "status",
                        str,
                        "Failure state: denied or error.",
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the failure."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="denied",
                fields=[
                    EventPayloadFieldSpec(
                        "status",
                        str,
                        "Always denied when permission is rejected.",
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the denial."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="timeout",
                fields=[
                    EventPayloadFieldSpec(
                        "status",
                        str,
                        "Always error when the request exceeds timeout.",
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive timeout error message."
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
        enable_high_accuracy: bool = True,
        timeout: int = 10000,
        maximum_age: int = 0,
        on_locate: UrlOrFunction | None = None,
        on_error: UrlOrFunction | None = None,
        on_denied: UrlOrFunction | None = None,
        on_timeout: UrlOrFunction | None = None,
        **extra_settings,
    ):
        """Initialize the CurrentLocation component.

        Args:
            name: The form field name for geolocation data.
            show: Whether to display the geolocation status UI.
            show_coordinates: Whether to display coordinates when available.
            enable_high_accuracy: Whether to prefer high-accuracy geolocation.
            timeout: Maximum time to wait for geolocation in milliseconds.
            maximum_age: Maximum age for cached location in milliseconds.
            on_locate: Function or URL to call when a location is resolved.
            on_error: Function or URL to call when geolocation fails.
            on_denied: Function or URL to call when permission is denied.
            on_timeout: Function or URL to call when geolocation times out.
            **extra_settings: Additional HTML attributes.
        """
        validate_parameter_name(name, "CurrentLocation")
        self.name = name
        self.show = show
        self.show_coordinates = show_coordinates
        self.enable_high_accuracy = enable_high_accuracy
        self.timeout = timeout
        self.maximum_age = maximum_age
        self.on_locate = on_locate
        self.on_error = on_error
        self.on_denied = on_denied
        self.on_timeout = on_timeout
        self.extra_settings = extra_settings


COMPONENT_CONTRACT_REGISTRY.register(CurrentLocation.CONTRACT)
