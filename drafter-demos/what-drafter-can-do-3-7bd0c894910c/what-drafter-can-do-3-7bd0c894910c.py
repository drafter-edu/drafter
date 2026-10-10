from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Tamagotchi Minute"),
        Clock(2000, "hungrier", show=False),
        Output("status", ["Captain is content."]),
        "\n",
        Button("Feed", "feed")
    ])


@route
def hungrier(state: State) -> Fragment:
    state.hunger = state.hunger + 1
    if state.hunger < 3:
        mood = "Captain is content."
    else:
        mood = "Captain demands salmon. (" + str(state.hunger) + ")"
    return Fragment([mood], target="#status")


@route
def feed(state: State) -> Page:
    state.hunger = 0
    return index(state)


start_server(State(0))
