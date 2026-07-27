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
        "Energy: " + str(state.energy)
    ])


start_server(State(5, 5))
