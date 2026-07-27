from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int
    energy: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hunger: " + str(state.hunger) + "\n",
        "Energy: " + str(state.energy) + "\n",
        Button("Feed", "feed")
    ])


@route
def feed(state: State) -> Page:
    state.hunger = state.hunger - 2
    if state.hunger < 0:
        state.hunger = 0
    return index(state)


start_server(State(5, 5))
