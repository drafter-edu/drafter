from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hours: float


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Nap Log"),
        "Captain napped for " + str(state.hours) + " hours.\n",
        Slider("hours", 0, 12, state.hours, step=0.5),
        "\n",
        Button("Record", "record")
    ])


@route
def record(state: State, hours: float) -> Page:
    state.hours = hours
    return index(state)


start_server(State(2.5))
