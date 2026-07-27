from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    sightings: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Backyard Sightings"),
        BulletedList(state.sightings),
        "Report a sighting:",
        TextBox("creature"),
        "\n",
        Button("Log it", "log")
    ])


@route
def log(state: State, creature: str) -> Page:
    state.sightings.append(creature)
    return index(state)


start_server(State(["one bold squirrel"]))
