from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    collar: Color


@route
def index(state: State) -> Page:
    darker = Color(state.collar.red // 2, state.collar.green // 2,
                   state.collar.blue // 2)
    return Page(state, [
        Span("Babbage's collar", style_color=state.collar,
             style_font_weight="bold"),
        "\n",
        Span("and its shadow", style_color=darker),
        "\nPick a color:",
        ColorPicker("collar", state.collar),
        "\n",
        Button("Try it on", "try_on")
    ])


@route
def try_on(state: State, collar: Color) -> Page:
    state.collar = collar
    return index(state)


start_server(State(Color(51, 102, 255)))
