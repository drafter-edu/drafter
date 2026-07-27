from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "The last total was " + str(state.total) + ".\n",
        "Pick two whole numbers to add:",
        TextBox("first", 3),
        TextBox("second", 4),
        "\n",
        Button("Add them", "add")
    ])


@route
def add(state: State, first: int, second: int) -> Page:
    state.total = first + second
    return index(state)


assert_state(add(State(0), 3, 4), State(7))

start_server(State(0))
