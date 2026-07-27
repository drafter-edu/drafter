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
        Button("Reset", "reset_count")
    ])


@route
def increment(state: State) -> Page:
    state.count = state.count + 1
    return index(state)


@route
def reset_count(state: State) -> Page:
    state.count = 0
    return index(state)


assert_state(increment(State(0)), State(1))
assert_state(reset_count(State(7)), State(0))
assert_has(index(State(3)), "Current count: 3")

start_server(State(0))
