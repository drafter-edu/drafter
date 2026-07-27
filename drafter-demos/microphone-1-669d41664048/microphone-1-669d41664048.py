from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    barks: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Bark Counter"),
        Output("count", ["Barks detected: " + str(state.barks)]),
        "\n",
        Microphone("mic", threshold=0.6, cooldown=500,
                   on_loud="bark"),
        "\n",
        "Every loud noise counts as one bark. Ada disputes "
        "the methodology."
    ])


@route
def bark(state: State) -> Fragment:
    state.barks = state.barks + 1
    return Fragment(["Barks detected: " + str(state.barks)],
                    target="#count")


start_server(State(0))
