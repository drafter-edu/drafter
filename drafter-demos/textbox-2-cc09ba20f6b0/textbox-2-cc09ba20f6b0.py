from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Total so far: " + str(state.total) + "\n",
        "Add this much:",
        TextBox("amount", 5),
        "\n",
        Button("Add", "add")
    ])


@route
def add(state: State, amount: int) -> Page:
    state.total = state.total + amount
    return index(state)


start_server(State(0))
