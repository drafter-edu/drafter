from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    visits: int


@route
def index(state: State) -> Page:
    state.visits = state.visits + 1
    return Page(state, [
        "This page has been built " + str(state.visits) + " times.\n",
        Button("Build it again", "index")
    ])


assert_state(index(State(0)), State(1))

start_server(State(0))
