from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    message: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "The zoo says: " + state.message + "\n",
        Button("Visit again", "index"),
    ])


start_server(State("hello"))
