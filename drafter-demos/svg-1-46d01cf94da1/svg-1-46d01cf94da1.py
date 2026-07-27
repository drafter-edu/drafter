from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    slices_eaten: int


@route
def index(state: State) -> Page:
    pizza = '<circle cx="50" cy="50" r="45" fill="gold" />'
    for slice_number in range(state.slices_eaten):
        angle = slice_number * 45
        pizza = pizza + (
            '<line x1="50" y1="50" x2="95" y2="50" stroke="white" '
            'stroke-width="8" transform="rotate(' + str(angle)
            + ' 50 50)" />'
        )
    return Page(state, [
        Header("Pizza Tracker"),
        SVG(pizza, width=150, height=150, viewBox="0 0 100 100"),
        "\n",
        Button("Eat a slice", "eat")
    ])


@route
def eat(state: State) -> Page:
    state.slices_eaten = min(8, state.slices_eaten + 1)
    return index(state)


start_server(State(0))
