from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    count: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current count: " + str(state.count) + "\n",
        Button("+1", "increment"),
        Button("-1", "decrement"),
        Button("Reset", "reset_count")
    ])


@route
def increment(state: State) -> Page:
    state.count = state.count + 1
    return index(state)


@route
def decrement(state: State) -> Page:
    state.count = state.count - 1
    return index(state)


@route
def reset_count(state: State) -> Page:
    state.count = 0
    return index(state)


start_server(State(0))
