from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Hello, " + state.name + "!"),
        "Your name: ",
        TextBox("new_name"),
        Button("Save", "save_name")
    ])


@route
def save_name(state: State, new_name: str) -> Page:
    state.name = new_name
    return index(state)


assert_has(save_name(State("stranger"), "Ada"), Header("Hello, Ada!"))

start_server(State("stranger"))
