from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    presses: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Text("Big red button protocol.\n", style_font_size="20px"),
        Button("Do not press", "press",
               style_background_color="crimson",
               style_color="white",
               style_padding="10px")
    ])


@route
def press(state: State) -> Page:
    state.presses = state.presses + 1
    return Page(state, [
        "Pressed " + str(state.presses) + " times. Naturally.\n",
        Button("Back", "index")
    ])


start_server(State(0))
