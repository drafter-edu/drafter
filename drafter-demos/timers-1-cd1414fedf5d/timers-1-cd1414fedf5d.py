from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    answered: bool


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Quick! 10 seconds!"),
        "Which pet is the grey cat?\n",
        Timer(10000, "too_slow"),
        "\n",
        Button("Ada", "wrong"),
        Button("Captain", "right"),
        Button("Domino", "wrong")
    ])


@route
def right(state: State) -> Page:
    state.answered = True
    return Page(state, ["Correct, with time to spare."])


@route
def wrong(state: State) -> Page:
    state.answered = True
    return Page(state, ["Wrong, but at least you were fast."])


@route
def too_slow(state: State) -> Page:
    return Page(state, ["Time ran out before you chose!"])


start_server(State(False))
