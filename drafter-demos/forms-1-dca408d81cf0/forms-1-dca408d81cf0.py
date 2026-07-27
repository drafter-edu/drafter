from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hello, " + state.name + "!\n",
        "Change my name:",
        TextBox("new_name", state.name),
        "\n",
        Button("Rename", "rename")
    ])


@route
def rename(state: State, new_name: str) -> Page:
    state.name = new_name
    return index(state)


start_server(State("stranger"))
