from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    count: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current count: " + str(state.count) + "\n",
        Button("Double it", "double_count")
    ])


@route
def double_count(state: State) -> Page:
    print("Before doubling:", state.count)
    state.count = state.count * 2
    print("After doubling:", state.count)
    return index(state)


start_server(State(1))
