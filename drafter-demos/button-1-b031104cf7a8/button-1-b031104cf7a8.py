from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Ada the corgi has had " + str(state.treats) + " treats.\n",
        Button("Give a treat", "feed")
    ])


@route
def feed(state: State) -> Page:
    state.treats = state.treats + 1
    return index(state)


start_server(State(0))
