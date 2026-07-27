from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    flavor: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current scoop: " + state.flavor + "\n",
        SelectBox("choice", ["vanilla", "pistachio", "blackberry"],
                  state.flavor),
        "\n",
        Button("Scoop it", "scoop")
    ])


@route
def scoop(state: State, choice: str) -> Page:
    state.flavor = choice
    return index(state)


start_server(State("vanilla"))
