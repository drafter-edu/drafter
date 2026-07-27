from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clicks: int


@route
def index(state: State) -> Page:
    print("Rendering index with", state.clicks, "clicks")
    return Page(state, [
        "Clicks: " + str(state.clicks) + "\n",
        Button("Click me", "add_one")
    ])


@route
def add_one(state: State) -> Page:
    print("add_one is running")
    state.clicks = state.clicks + 1
    return index(state)


start_server(State(0))
