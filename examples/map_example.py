from drafter import *

hide_debug_information()


@dataclass
class State:
    stops: list


@route
def index(state: State):
    markers = [
        MapMarker(stop.latitude, stop.longitude, f"Stop {i + 1}")
        for i, stop in enumerate(state.stops)
    ]
    return Page(
        state,
        [
            "Click the map to add a stop!",
            Map(
                "spot",
                center=MapLocation(39.68, -75.75),
                markers=markers,
                height=360,
                on_click=add_stop,
                on_marker_click=clicked_marker,
            ),
            Paragraph("You have", Span(f"{len(state.stops)}", id="length"), "stops."),
            Paragraph("click on a marker to see its info", id="info"),
        ],
    )


@route
def add_stop(state: State, spot: MapLocation, add_marker: AddMarkerFunction):
    state.stops.append(spot)
    add_marker(f"Stop {len(state.stops)}")
    return Fragment(state, f"{len(state.stops)}", target="#length")


@route
def clicked_marker(state: State, latitude: float, longitude: float, label: str):
    return Fragment(
        state,
        Paragraph(
            f"Clicked marker at latitude: {latitude}, longitude: {longitude}, label: {label}"
        ),
        target="#info",
    )


start_server(State([]))
