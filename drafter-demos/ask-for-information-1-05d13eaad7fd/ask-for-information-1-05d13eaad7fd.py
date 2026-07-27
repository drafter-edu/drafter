from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "What should we call you?",
        TextBox("name"),
        "\n",
        Button("Save", "save_name")
    ])


@route
def save_name(state: State, name: str) -> Page:
    state.name = name
    return Page(state, [
        "Nice to meet you, " + state.name + "!\n",
        Button("Change it", "index")
    ])


start_server(State(""))
