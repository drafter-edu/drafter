from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    size: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Ordered size: " + state.size + "\n",
        RadioButtonGroup("picked", ["small", "medium", "absurd"],
                         state.size),
        "\n",
        Button("Order", "order")
    ])


@route
def order(state: State, picked: str) -> Page:
    state.size = picked
    return index(state)


start_server(State("small"))
