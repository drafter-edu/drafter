from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    art: Picture


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("One-Button Art Studio"),
        state.art,
        "\n",
        Button("Rotate", "spin"),
        Button("Shrink", "shrink"),
        Button("Drain the color", "drain")
    ])


@route
def spin(state: State) -> Page:
    state.art = state.art.rotate(90)
    return index(state)


@route
def shrink(state: State) -> Page:
    state.art = state.art.scale(0.5)
    return index(state)


@route
def drain(state: State) -> Page:
    state.art = state.art.grayscale()
    return index(state)


start_server(State(Picture.new(150, 100, "tomato")))
