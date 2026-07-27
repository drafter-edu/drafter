from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    water_level: int


@route
def index(state: State) -> Page:
    if state.water_level > 0:
        status = "The plant is fine. Water level: " + str(state.water_level)
    else:
        status = "The plant is THIRSTY."
    return Page(state, [
        Header("Plant Monitor"),
        status + "\n",
        Button("Water it", "water"),
        Button("Wait a day", "wait")
    ])


@route
def water(state: State) -> Page:
    state.water_level = 3
    return index(state)


@route
def wait(state: State) -> Page:
    if state.water_level > 0:
        state.water_level = state.water_level - 1
    return index(state)


start_server(State(2))
