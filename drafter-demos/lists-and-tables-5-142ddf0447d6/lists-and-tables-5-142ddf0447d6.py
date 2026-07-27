from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    done: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Homework Machine"),
        "Problems done: " + str(state.done) + " of 10\n",
        ProgressBar(state.done, 10),
        "\nEnthusiasm remaining:\n",
        Meter(10 - state.done, 0, 10),
        "\n",
        Button("Do a problem", "work")
    ])


@route
def work(state: State) -> Page:
    if state.done < 10:
        state.done = state.done + 1
    return index(state)


start_server(State(3))
