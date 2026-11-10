from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    size: int
    color: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Span("Domino", style_font_size=str(state.size) + "px",
             style_color=state.color),
        "\nSize:",
        Slider("size", 12, 60, state.size),
        "\nColor:",
        ColorPicker("color", state.color),
        "\n",
        Button("Restyle", "restyle")
    ])


@route
def restyle(state: State, size: int, color: str) -> Page:
    state.size = size
    state.color = color
    return index(state)


start_server(State(24, "#3366ff"))
