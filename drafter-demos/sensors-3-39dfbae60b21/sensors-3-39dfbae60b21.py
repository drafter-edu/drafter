from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pins: list[MapMarker]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Squirrel Sightings"),
        "Click where the squirrel was.\n",
        Map("spot", center=(39.68, -75.75), zoom=15,
            markers=state.pins, on_click="sighting")
    ])


@route
def sighting(state: State, latitude: float, longitude: float) -> Page:
    state.pins.append(MapMarker(latitude, longitude, "squirrel"))
    return index(state)


start_server(State([]))
