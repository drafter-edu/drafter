from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    roast: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Marshmallow Station"),
        "Current roast: " + state.roast + "\n",
        RadioButtonGroup("level",
                         ["barely warm", "golden", "on fire"],
                         state.roast),
        "\n",
        Button("Roast", "roast_it")
    ])


@route
def roast_it(state: State, level: str) -> Page:
    state.roast = level
    return index(state)


start_server(State("golden"))
