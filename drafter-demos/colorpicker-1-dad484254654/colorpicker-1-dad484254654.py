from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    collar: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Collar Shop"),
        Span("Babbage's new collar", style_color=state.collar,
             style_font_weight="bold"),
        "\nPick a color:",
        ColorPicker("collar", state.collar),
        "\n",
        Button("Try it on", "try_on")
    ])


@route
def try_on(state: State, collar: str) -> Page:
    state.collar = collar
    return index(state)


start_server(State("royalblue"))
