from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    destination: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Trip Planner"),
        "Current destination: " + state.destination + "\n",
        SelectBox("choice",
                  ["aquarium", "museum", "volcano", "library"],
                  state.destination),
        "\n",
        Button("Choose", "choose")
    ])


@route
def choose(state: State, choice: str) -> Page:
    state.destination = choice
    return index(state)


start_server(State("aquarium"))
