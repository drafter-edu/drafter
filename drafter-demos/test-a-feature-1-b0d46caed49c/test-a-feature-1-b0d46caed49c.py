from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Cookie Game"),
        "Your score is " + str(state.score) + "\n",
        Button("Click me!", "add_point")
    ])


@route
def add_point(state: State) -> Page:
    state.score = state.score + 1
    return index(state)


assert_state(add_point(State(5)), State(6))
assert_has(index(State(5)), "Your score is 5")
assert_has(index(State(5)), Button("Click me!", "add_point"))

start_server(State(0))
