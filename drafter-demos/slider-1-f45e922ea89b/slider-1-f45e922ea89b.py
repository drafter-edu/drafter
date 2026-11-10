from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Treat Planner"),
        "Ada the corgi gets " + str(state.treats) + " treats today.\n",
        "Fewer",
        Slider("treats", 0, 10, state.treats),
        "More\n",
        Button("Save", "save")
    ])


@route
def save(state: State, treats: int) -> Page:
    state.treats = treats
    return index(state)


start_server(State(3))
