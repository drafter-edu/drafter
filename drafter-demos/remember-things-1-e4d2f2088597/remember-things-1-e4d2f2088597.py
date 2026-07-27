from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int
    best: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        "Best so far: " + str(state.best) + "\n",
        Button("Score a point", "add_point"),
        Button("Lose a point", "lose_point")
    ])


@route
def add_point(state: State) -> Page:
    state.score = state.score + 1
    if state.score > state.best:
        state.best = state.score
    return index(state)


@route
def lose_point(state: State) -> Page:
    state.score = state.score - 1
    if state.score < 0:
        state.score = 0
    return index(state)


assert_state(add_point(State(0, 0)), State(1, 1))
assert_state(add_point(State(2, 9)), State(3, 9))
assert_state(lose_point(State(3, 9)), State(2, 9))

start_server(State(0, 0))
