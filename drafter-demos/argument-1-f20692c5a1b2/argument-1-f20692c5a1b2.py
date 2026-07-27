from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    last_wish: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "The genie last heard: " + state.last_wish + "\n",
        Button("Wish for gold", "wish", [Argument("wish_for", "gold")]),
        Button("Wish for time", "wish", [Argument("wish_for", "time")]),
        Button("Wish for naps", "wish", [Argument("wish_for", "naps")])
    ])


@route
def wish(state: State, wish_for: str) -> Page:
    state.last_wish = wish_for
    return index(state)


start_server(State("nothing yet"))
