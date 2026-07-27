from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Captain's Treat Counter"),
        "Treats given: " + str(state.treats) + "\n",
        TextBox("amount", "1"),
        "\n",
        Button("Give treats", "give")
    ])


@route
def give(state: State, amount: int) -> Page:
    state.treats = state.treats + amount
    return index(state)


assert_state(give(State(0), 3), State(3))

start_server(State(0))
