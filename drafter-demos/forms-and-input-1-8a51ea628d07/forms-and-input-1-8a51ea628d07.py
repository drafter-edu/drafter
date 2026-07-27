from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "What is your name?",
        TextBox("new_name"),
        "\n",
        Button("Greet me", "greet")
    ])


@route
def greet(state: State, new_name: str) -> Page:
    state.name = new_name
    return Page(state, [
        "Hello, " + state.name + "!\n",
        Button("Start over", "index")
    ])


assert_state(greet(State(""), "Ada"), State("Ada"))

start_server(State(""))
