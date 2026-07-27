from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    visits: int


@route
def index(state: State) -> Page:
    state.visits = state.visits + 1
    return Page(state, [
        "Visits so far: " + str(state.visits) + "\n",
        Button("Visit again", "index")
    ])


start_server(State(0))
