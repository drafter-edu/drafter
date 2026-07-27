from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Idle Corgi"),
        "Ada finds a treat every second, and two when you help.\n",
        Clock(1000, "tick", show=False),
        Output("score", ["Treats: " + str(state.treats)]),
        "\n",
        Button("Help her look", "help_look")
    ])


@route
def tick(state: State) -> Fragment:
    state.treats = state.treats + 1
    return Fragment(["Treats: " + str(state.treats)],
                    target="#score")


@route
def help_look(state: State) -> Page:
    state.treats = state.treats + 2
    return index(state)


start_server(State(0))
