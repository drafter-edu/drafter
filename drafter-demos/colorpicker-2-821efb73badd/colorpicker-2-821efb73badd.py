from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    amounts: list[int]


@route
def index(state: State) -> Page:
    brightness = sum(state.amounts) // 3
    return Page(state, [
        Header("How bright is it?"),
        "Red, green, blue: " + str(state.amounts),
        "\nBrightness out of 255: " + str(brightness),
        "\n",
        ColorPicker("paint", state.amounts),
        "\n",
        Button("Measure", "measure")
    ])


@route
def measure(state: State, paint: list[int]) -> Page:
    state.amounts = paint
    return index(state)


start_server(State([255, 136, 0]))
