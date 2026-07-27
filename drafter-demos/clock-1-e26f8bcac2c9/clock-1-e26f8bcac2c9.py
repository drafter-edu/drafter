from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    position: int


CAPTIONS = [
    "Ada guards the front window.",
    "Babbage has located a sunbeam.",
    "Captain judges everyone from the shelf.",
    "Domino is somewhere. Probably."
]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet Cam Highlights"),
        Clock(3000, "advance", show=False),
        Output("caption", [CAPTIONS[state.position]])
    ])


@route
def advance(state: State) -> Fragment:
    state.position = (state.position + 1) % len(CAPTIONS)
    return Fragment([CAPTIONS[state.position]], target="#caption")


start_server(State(0))
