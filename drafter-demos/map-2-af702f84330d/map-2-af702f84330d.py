from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    sightings: list[MapMarker]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Domino Sighting Tracker"),
        "Click the map where you spotted the cat.\n",
        "Sightings: " + str(len(state.sightings)) + "\n",
        Map("spot",
            center=(39.68, -75.75),
            zoom=15,
            markers=state.sightings,
            on_click="record")
    ])


@route
def record(state: State, latitude: float, longitude: float) -> Page:
    state.sightings.append(MapMarker(latitude, longitude, "Domino!"))
    return index(state)


start_server(State([]))
