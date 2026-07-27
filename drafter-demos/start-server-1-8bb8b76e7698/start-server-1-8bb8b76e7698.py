from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        Button("Add a point", "gain")
    ])


@route
def gain(state: State) -> Page:
    state.score = state.score + 1
    return index(state)


start_server(State(0))
