from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "The jar holds " + str(state.total) + " marbles.\n",
        "Add how many?",
        TextBox("amount", 1),
        "\n",
        Button("Add", "add")
    ])


@route
def add(state: State, amount: int) -> Page:
    state.total = state.total + amount
    return index(state)


start_server(State(10))
