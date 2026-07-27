from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    activity: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Captain the cat is currently: " + state.activity + "\n",
        Button("Nap time", "act", [Argument("choice", "napping")]),
        Button("Play time", "act", [Argument("choice", "playing")])
    ])


@route
def act(state: State, choice: str) -> Page:
    state.activity = choice
    return index(state)


start_server(State("sitting"))
