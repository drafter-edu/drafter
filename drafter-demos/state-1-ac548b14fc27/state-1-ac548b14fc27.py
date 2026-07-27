from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        Button("Score a point", "add_point")
    ])


@route
def add_point(state: State) -> Page:
    state.score = state.score + 1
    return index(state)


assert_state(add_point(State(0)), State(1))

start_server(State(0))
