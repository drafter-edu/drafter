from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    shout: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Echo Chamber"),
        "You said: " + state.shout + "\n",
        TextBox("message"),
        "\n",
        Button("Shout", "shout_it")
    ])


@route
def shout_it(state: State, message: str) -> Page:
    state.shout = message
    return index(state)


start_server(State("nothing yet"))
