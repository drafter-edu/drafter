from drafter import *
from dataclasses import dataclass
from datetime import time


@dataclass
class State:
    dinner: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Cat Feeding Schedule"),
        "Captain eats dinner at: " + state.dinner + "\n",
        "New dinner time:",
        TimeInput("when", state.dinner),
        "\n",
        Button("Update", "update")
    ])


@route
def update(state: State, when: time) -> Page:
    state.dinner = when.isoformat(timespec="minutes")
    return index(state)


start_server(State("17:00"))
