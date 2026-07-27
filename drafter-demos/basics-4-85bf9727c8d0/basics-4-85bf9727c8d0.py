from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clicks: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Clicks so far: " + str(state.clicks) + "\n",
        Button("Click me", "add_one")
    ])


@route
def add_one(state: State) -> Page:
    state.clicks = state.clicks + 1
    return index(state)


start_server(State(40))
