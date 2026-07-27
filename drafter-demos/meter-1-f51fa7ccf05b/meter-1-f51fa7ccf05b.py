from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Kennel Dashboard"),
        "Ada's hunger:\n",
        Meter(state.hunger, min=0, max=100,
              low=30, high=70, optimum=10),
        "\n",
        Button("Feed her", "feed"),
        Button("Wait an hour", "wait")
    ])


@route
def feed(state: State) -> Page:
    state.hunger = 0
    return index(state)


@route
def wait(state: State) -> Page:
    state.hunger = min(100, state.hunger + 30)
    return index(state)


start_server(State(50))
