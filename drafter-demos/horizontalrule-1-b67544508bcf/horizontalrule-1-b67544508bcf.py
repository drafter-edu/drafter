from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    signed_in: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Guest Book"),
        "Guests so far: " + str(state.signed_in) + "\n",
        HorizontalRule(),
        "Add yourself:",
        TextBox("guest_name"),
        "\n",
        Button("Sign", "sign")
    ])


@route
def sign(state: State, guest_name: str) -> Page:
    state.signed_in = state.signed_in + 1
    return index(state)


start_server(State(0))
