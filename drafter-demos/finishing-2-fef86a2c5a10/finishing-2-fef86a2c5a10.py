from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    compliments: list[str]
    position: int


COMPLIMENTS = [
    "Your code is looking sharp today.",
    "Ada the corgi would sit for you.",
    "You debug with style."
]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Compliment Machine"),
        state.compliments[state.position] + "\n",
        Button("Another, please", "another")
    ])


@route
def another(state: State) -> Page:
    state.position = state.position + 1
    if state.position >= len(state.compliments):
        state.position = 0
    return index(state)


start_server(State(COMPLIMENTS, 0))
