from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    paint: Color


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Window Paint"),
        Div("Domino is hiding behind this.",
            style_background_color=state.paint, style_padding="12px"),
        "\nOpacity out of 255: " + str(state.paint.alpha),
        "\n",
        ColorPicker("paint", state.paint, alpha=True),
        "\n",
        Button("Repaint", "repaint")
    ])


@route
def repaint(state: State, paint: Color) -> Page:
    state.paint = paint
    return index(state)


start_server(State(Color(51, 102, 255, 128)))
