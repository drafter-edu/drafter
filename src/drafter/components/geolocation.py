"""Geolocation components for requesting and displaying location data.

Provides the CurrentLocation component and Location dataclass for handling
browser geolocation API integration with form-based workflows.

CurrentLocation is a *hybrid component*: the Python class renders a
``<drafter-geolocation>`` custom HTML element, and the matching TypeScript
class (``js/src/components/geolocation.tsx``) handles the browser-side
Geolocation API, UI state management, and custom event dispatch.
"""

from dataclasses import dataclass
from typing import Optional, Literal
from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction
from drafter.components.utilities.validation import validate_parameter_name


LocationStatus = Literal[
    "unavailable", "prompt", "granted", "denied", "pending", "error"
]


@dataclass
class Location:
    """Geolocation data from the browser's geolocation API.

    Attributes:
        status: Current permission/availability state.
        message: Optional descriptive message about the status.
        lat: Latitude in decimal degrees (None if unavailable).
        lon: Longitude in decimal degrees (None if unavailable).
        accuracy: Position accuracy in meters (None if unavailable).
        altitude: Altitude in meters above sea level (None if unavailable).
        heading: Direction of travel in degrees (None if unavailable).
        speed: Speed in meters per second (None if unavailable).
        timestamp: Unix timestamp of position acquisition (None if unavailable).
    """

    status: LocationStatus
    message: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    timestamp: Optional[float] = None


@dataclass(repr=False)
class CurrentLocation(Component):
    """A component that requests and displays browser geolocation.

    Rendered as a ``<drafter-geolocation>`` custom HTML element whose
    behavior is implemented in TypeScript (``js/src/components/geolocation.tsx``).
    The element creates a hidden form input that stores JSON-serialised
    location data, so the component works both in plain form-submission flows
    and in event-driven flows via the optional callback parameters.

    **Form-submission usage** — location data arrives as a ``Location`` parameter
    when the user clicks a submit button::

        CurrentLocation("loc")
        Button("Submit", process)

        @route
        def process(state, loc: Location): ...

    **Event-driven usage** — a route is called immediately once the browser
    grants or denies permission, without requiring a button press::

        CurrentLocation("loc", on_grant=location_received)

        @route
        def location_received(state, lat: float, lon: float, accuracy: float): ...

    Visual states (managed entirely in JS):

    - **prompt**: "Use my location" button shown before permission is requested.
    - **pending**: Spinner while waiting for the browser permission prompt.
    - **denied**: Message shown when the user blocks location access.
    - **granted**: Success message; optionally shows coordinates.
    - **error**: Error message for non-denial failures (timeout, unavailable).
    - **unavailable**: Message when the Geolocation API is not supported.

    Attributes:
        name: Form field name used for the hidden location input.
        show_coordinates: Display lat/lon once granted (default: ``False``).
        on_grant: Route called when location is granted, receiving the location
            fields (``lat``, ``lon``, ``accuracy``, ``altitude``, ``heading``,
            ``speed``, ``timestamp``) as keyword arguments.
        on_deny: Route called when the user denies location access.
        on_error: Route called on a non-denial geolocation error, receiving
            ``status`` and ``message`` keyword arguments.
        on_unavailable: Route called when the Geolocation API is not available.
    """

    name: str
    show_coordinates: bool = False
    on_grant: Optional[UrlOrFunction] = None
    on_deny: Optional[UrlOrFunction] = None
    on_error: Optional[UrlOrFunction] = None
    on_unavailable: Optional[UrlOrFunction] = None

    tag = "drafter-geolocation"

    RENAME_ATTRS = {"show_coordinates": "show-coordinates"}
    KNOWN_ATTRS = ["name", "show-coordinates"]
    EXTRA_SUPPORTED_EVENTS = ["grant", "deny", "error", "unavailable"]

    ARGUMENTS = [
        ComponentArgument("name", "positional"),
        ComponentArgument("show_coordinates", "keyword", False),
        ComponentArgument("on_grant", "keyword", None, is_event=True),
        ComponentArgument("on_deny", "keyword", None, is_event=True),
        ComponentArgument("on_error", "keyword", None, is_event=True),
        ComponentArgument("on_unavailable", "keyword", None, is_event=True),
    ]

    def __init__(
        self,
        name: str,
        show_coordinates: bool = False,
        on_grant: Optional[UrlOrFunction] = None,
        on_deny: Optional[UrlOrFunction] = None,
        on_error: Optional[UrlOrFunction] = None,
        on_unavailable: Optional[UrlOrFunction] = None,
        **extra_settings,
    ):
        """Initialise the CurrentLocation component.

        Args:
            name: Form field name for location data.
            show_coordinates: Whether to display coordinates when available.
            on_grant: Route called when location is granted.
            on_deny: Route called when location is denied.
            on_error: Route called on a geolocation error.
            on_unavailable: Route called when geolocation is not supported.
            **extra_settings: Additional HTML attributes.
        """
        validate_parameter_name(name, "CurrentLocation")
        self.name = name
        self.show_coordinates = show_coordinates
        self.on_grant = on_grant
        self.on_deny = on_deny
        self.on_error = on_error
        self.on_unavailable = on_unavailable
        self.extra_settings = extra_settings

    def get_id(self) -> str:
        """Return a stable element ID based on the field name."""
        return self.extra_settings.get("id", f"drafter-geolocation-{self.name}")
