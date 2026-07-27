from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    motto: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current motto: " + state.motto + "\n",
        "A new motto:",
        TextBox("new_motto", state.motto),
        "\n",
        Button("Update", "update")
    ])


@route
def update(state: State, new_motto: str) -> Page:
    state.motto = new_motto
    return index(state)


start_server(State("Onward!"))
