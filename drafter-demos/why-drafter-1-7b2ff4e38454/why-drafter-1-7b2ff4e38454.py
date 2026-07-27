from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Trivia: Dogs"),
        "Is Ada a corgi? Score: " + str(state.score) + "\n",
        Button("Yes", "correct"),
        Button("No", "index")
    ])


@route
def correct(state: State) -> Page:
    state.score = state.score + 1
    return index(state)


assert_state(correct(State(0)), State(1))

start_server(State(0))
