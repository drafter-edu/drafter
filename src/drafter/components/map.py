"""Interactive map component backed by Leaflet.

Provides the Map component plus the MapLocation, MapMarker, and MapView
dataclasses for working with geographic data in student applications.

The Python side only describes the component: it renders as a
``<drafter-map>`` custom element whose behavior (Leaflet map, tiles,
markers, interaction events) is implemented in js/src/components/map.tsx.
The element keeps a hidden form field named after the component updated
with the JSON-encoded location of the most recent click, so a route
parameter with the same name annotated as :class:`MapLocation` receives
the converted value. Map tiles come from OpenStreetMap and require an
internet connection; the JavaScript side degrades gracefully offline.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass

from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction
from drafter.components.utilities.contracts import (
    ComponentContract,
    EventPayloadFieldSpec,
    EventPayloadSpec,
    HelperContext,
    HelperSpec,
)
from drafter.components.utilities.persistence import (
    PERSIST_KEY_ATTR,
    derive_persist_key,
)
from drafter.components.utilities.registry import (
    COMPONENT_CONTRACT_REGISTRY,
    CONVERTER_REGISTRY,
)
from drafter.components.utilities.validation import validate_parameter_name
from drafter.data.converter import ConversionContext, ConversionResult
from drafter.data.errors import StudentFacingError


@dataclass
class MapLocation:
    """A geographic point on a map.

    Attributes:
        latitude: Latitude in decimal degrees (positive is north).
        longitude: Longitude in decimal degrees (positive is east).
    """

    latitude: float
    longitude: float


@dataclass
class MapMarker:
    """A labeled point displayed on a :class:`Map`.

    Attributes:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.
        label: Optional text shown when hovering over the marker.
    """

    latitude: float
    longitude: float
    label: str = ""


@dataclass
class MapView:
    """The visible region of a :class:`Map` after panning or zooming.

    Attributes:
        latitude: Latitude of the map's center in decimal degrees.
        longitude: Longitude of the map's center in decimal degrees.
        zoom: The zoom level (higher is closer; ~2 is the whole world,
            ~13 is a town, ~18 is a street).
    """

    latitude: float
    longitude: float
    zoom: int


CenterValue = MapLocation | tuple | list | str | None
"""The accepted forms for a Map's `center`: a `MapLocation`, a
`(latitude, longitude)` pair, a `"latitude,longitude"` string, or None
for the default center (see `_normalize_center`)."""


def _normalize_center(center: CenterValue, component_name: str) -> MapLocation | None:
    """Accept a MapLocation, (lat, lng) pair, or "lat,lng" string."""
    if center is None or isinstance(center, MapLocation):
        return center
    if isinstance(center, (tuple, list)) and len(center) == 2:
        return MapLocation(float(center[0]), float(center[1]))
    if isinstance(center, str):
        parts = center.split(",")
        if len(parts) == 2:
            try:
                return MapLocation(float(parts[0]), float(parts[1]))
            except ValueError:
                pass
    raise StudentFacingError(
        f"Invalid center for {component_name}: {center!r}. "
        "Provide a MapLocation, a (latitude, longitude) pair, "
        'or a "latitude,longitude" string.',
        friendly=(
            f"The center argument you gave {component_name} is not something "
            "it can understand as a spot on the map; it needs a latitude "
            "and a longitude."
        ),
        steps=(
            "Pass a pair of numbers, like center=(40.7, -74.0).",
            "Or pass a MapLocation, like center=MapLocation(40.7, -74.0).",
            "Check that both numbers are real latitude/longitude values.",
        ),
    )


def _dataclass_converter(dataclass_type):
    """Build a converter turning a JSON string/dict payload into dataclass_type."""

    def convert(ctx: ConversionContext) -> ConversionResult | None:
        value = ctx.raw_value
        if isinstance(value, dataclass_type):
            return ConversionResult(ok=True, value=value)
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as error:
                return ConversionResult(
                    ok=False,
                    error_code="invalid_json",
                    message=f"Failed to parse {dataclass_type.__name__} data: {error}",
                )
        if isinstance(value, dict):
            try:
                return ConversionResult(ok=True, value=dataclass_type(**value))
            except TypeError as error:
                return ConversionResult(
                    ok=False,
                    error_code="invalid_fields",
                    message=f"Failed to build {dataclass_type.__name__}: {error}",
                )
        return None

    return convert


def _create_predicate_function(_map_type):
    def predicate(target, _cls=_map_type):
        return target is _cls

    return predicate


for _map_type in (MapLocation, MapMarker, MapView):
    CONVERTER_REGISTRY.register_predicate(
        _create_predicate_function(_map_type),
        _dataclass_converter(_map_type),
        priority=20,
        name=_map_type.__name__,
    )


def _make_add_marker(context: HelperContext):
    """Build the ``add_marker`` helper injected into Map event routes.

    The helper closes over the live ``<drafter-map>`` element and the event's
    coordinates; calling it appends a pin to the element's ``markers``
    attribute, which the JS side observes and applies to the running Leaflet
    map at once. This only changes the live map: the next full page render
    shows whatever ``Map(markers=...)`` receives, so routes should also
    record the location in their state.
    """
    element = context.element
    latitude = context.values.get("latitude")
    longitude = context.values.get("longitude")

    def add_marker(label: str = "") -> None:
        """Add a pin to the live map at the event's location.

        TODO: Add more robust error checking and ensure validity of call.

        Args:
            label: Optional text shown when hovering over the new pin.

        """
        raw = element.getAttribute("markers")
        markers = json.loads(raw) if raw else []
        markers.append(
            {"latitude": latitude, "longitude": longitude, "label": str(label)}
        )
        element.setAttribute("markers", json.dumps(markers))

    return add_marker


AddMarkerFunction = Callable[[str], None]
"""The type of the `add_marker` helper injected into routes handling Map
events: annotate a route parameter named `add_marker` with this, then
call it with an optional label to pin the event's location on the live
map (see `_make_add_marker`)."""


@dataclass(repr=False)
class Map(Component):
    """An interactive map that students can click, pan, and zoom.

    Renders an OpenStreetMap-based map (via Leaflet). Clicking the map,
    clicking a marker, or moving the view can each call a route function.
    The most recent clicked location is also kept in a hidden form field
    (named ``name``), so a route parameter with the same name annotated as
    :class:`MapLocation` receives the converted value on form submission.

    Note that map tiles are loaded from the internet; without a connection
    the map area shows a placeholder background but interactions still work.

    Attributes:
        name: The form field name that will contain the last clicked location.
        center: Where the map is initially centered: a :class:`MapLocation`,
            a ``(latitude, longitude)`` pair, or a ``"lat,lng"`` string.
        zoom: Initial zoom level (2 shows the whole world, 13 a town,
            18 a street). Defaults to 13.
        markers: A list of :class:`MapMarker` points to display.
        height: Height of the map in pixels. Defaults to 300.
        persistent: Whether the live map (including its current pan/zoom)
            survives page re-renders. Defaults to False.
        on_click: Function or URL to call when the map is clicked; the event
            provides ``latitude`` and ``longitude``.
        on_marker_click: Function or URL to call when a marker is clicked;
            the event provides ``latitude``, ``longitude``, and ``label``.
        on_move: Function or URL to call after the map is panned or zoomed;
            the event provides ``latitude``, ``longitude``, and ``zoom``.
    """

    name: str
    center: MapLocation | None = None
    zoom: int = 13
    markers: list | None = None
    height: int = 300
    persistent: bool = False
    on_click: UrlOrFunction | None = None
    on_marker_click: UrlOrFunction | None = None
    on_move: UrlOrFunction | None = None

    tag = "drafter-map"

    PERSISTABLE = True
    KNOWN_ATTRS = [
        "name",
        "center",
        "zoom",
        "markers",
        "height",
        "persistent",
    ]
    # Student-facing handler names map onto the custom events the element
    # dispatches ("pin"/"marker"/"view"); a native-named "click" event would
    # also fire for clicks on the zoom controls, so the DOM event is distinct.
    RENAME_ATTRS = {
        "on_click": "on_pin",
        "on_marker_click": "on_marker",
        "on_move": "on_view",
    }
    ARGUMENTS = [
        ComponentArgument("name", "positional"),
        ComponentArgument("center", "keyword", None),
        ComponentArgument("zoom", "keyword", 13),
        ComponentArgument("markers", "keyword", None),
        ComponentArgument("height", "keyword", 300),
        ComponentArgument("persistent", "keyword", False),
        ComponentArgument("on_click", "keyword", None, is_event=True),
        ComponentArgument("on_marker_click", "keyword", None, is_event=True),
        ComponentArgument("on_move", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["pin", "marker", "view"]

    #: What this component emits: the JS implementation (js/src/components/
    #: map.tsx) must match this contract, and the router uses it to reason
    #: about event payload fields.
    CONTRACT = ComponentContract(
        component_name="Map",
        html_tag="drafter-map",
        emitted_events=[
            EventPayloadSpec(
                event_name="pin",
                fields=[
                    EventPayloadFieldSpec(
                        "latitude", float, "Latitude of the clicked point."
                    ),
                    EventPayloadFieldSpec(
                        "longitude", float, "Longitude of the clicked point."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="marker",
                fields=[
                    EventPayloadFieldSpec(
                        "latitude", float, "Latitude of the clicked marker."
                    ),
                    EventPayloadFieldSpec(
                        "longitude", float, "Longitude of the clicked marker."
                    ),
                    EventPayloadFieldSpec(
                        "label", str, "Label of the clicked marker (may be empty)."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="view",
                fields=[
                    EventPayloadFieldSpec(
                        "latitude", float, "Latitude of the new map center."
                    ),
                    EventPayloadFieldSpec(
                        "longitude", float, "Longitude of the new map center."
                    ),
                    EventPayloadFieldSpec("zoom", int, "The new zoom level."),
                ],
            ),
        ],
        provided_helpers=[
            HelperSpec(
                name="add_marker",
                factory=_make_add_marker,
                documentation=(
                    "add_marker(label: str = '') adds a pin to the live map "
                    "at the clicked location, without re-rendering the page."
                ),
                events=("pin", "marker"),
            ),
        ],
    )

    def __init__(
        self,
        name: str,
        center: CenterValue = None,
        zoom: int = 13,
        markers: list | None = None,
        height: int = 300,
        persistent: bool = False,
        on_click: UrlOrFunction | None = None,
        on_marker_click: UrlOrFunction | None = None,
        on_move: UrlOrFunction | None = None,
        **extra_settings,
    ):
        """Initialize the Map component.

        Args:
            name: The form field name for the last clicked location.
            center: Initial map center (MapLocation, (lat, lng), or "lat,lng").
            zoom: Initial zoom level.
            markers: List of MapMarker points to display.
            height: Height of the map in pixels.
            persistent: Whether the live map survives page re-renders.
            on_click: Function or URL to call when the map is clicked.
            on_marker_click: Function or URL to call when a marker is clicked.
            on_move: Function or URL to call after panning or zooming.
            **extra_settings: Additional HTML attributes.
        """
        validate_parameter_name(name, "Map")
        self.name = name
        self.center = _normalize_center(center, "Map")
        self.zoom = zoom
        self.markers = self._normalize_markers(markers)
        self.height = height
        self.persistent = persistent
        self.on_click = on_click
        self.on_marker_click = on_marker_click
        self.on_move = on_move
        self.extra_settings = extra_settings

    @staticmethod
    def _normalize_markers(markers: list | None) -> list | None:
        if markers is None:
            return None
        normalized = []
        for marker in markers:
            if isinstance(marker, MapMarker):
                normalized.append(marker)
            elif isinstance(marker, MapLocation):
                normalized.append(MapMarker(marker.latitude, marker.longitude))
            elif isinstance(marker, (tuple, list)) and len(marker) in (2, 3):
                normalized.append(MapMarker(*marker))
            else:
                raise StudentFacingError(
                    f"Invalid marker for Map: {marker!r}. Provide a MapMarker, "
                    "a MapLocation, or a (latitude, longitude, label?) pair.",
                    friendly=(
                        "One of the markers you gave the Map is not something "
                        "it can understand as a point; each marker needs a "
                        "latitude and a longitude (and optionally a label)."
                    ),
                    steps=(
                        "Write each marker as a pair of numbers, like "
                        "markers=[(40.7, -74.0)].",
                        "Add an optional label as a third item, like "
                        "(40.7, -74.0, 'New York').",
                        "Or use MapMarker, like markers=[MapMarker(40.7, -74.0)].",
                    ),
                )
        return normalized

    def get_attributes(self, context) -> dict:
        """Extend the base attributes with DOM-ready center/marker strings.

        Converts the `center` MapLocation to a `"lat,lng"` string and the
        `markers` list to JSON (dropping either when None), and derives
        the persistence key from the form field name alone so updating a
        persistent map's markers does not evict the parked element.

        Args:
            context: The render context passed through to the base class.

        Returns:
            The attribute dictionary for the `<drafter-map>` element.
        """
        attributes = super().get_attributes(context)
        # The dataclass values must reach the DOM as strings the custom
        # element can parse: "lat,lng" for center, JSON for markers.
        center = attributes.get("center")
        if isinstance(center, MapLocation):
            attributes["center"] = f"{center.latitude},{center.longitude}"
        elif center is None:
            attributes.pop("center", None)
        markers = attributes.get("markers")
        if isinstance(markers, list):
            attributes["markers"] = json.dumps(
                [
                    {
                        "latitude": marker.latitude,
                        "longitude": marker.longitude,
                        "label": marker.label,
                    }
                    for marker in markers
                ]
            )
        elif markers is None:
            attributes.pop("markers", None)
        # Persistence identity must not include markers/center/zoom: adding a
        # stop to a persistent map should update the parked element, not evict
        # it. The form field name is the map's stable identity instead.
        if PERSIST_KEY_ATTR in attributes and "id" not in attributes:
            attributes[PERSIST_KEY_ATTR] = derive_persist_key(
                self.tag, {"name": self.name}
            )
        return attributes


COMPONENT_CONTRACT_REGISTRY.register(Map.CONTRACT)
