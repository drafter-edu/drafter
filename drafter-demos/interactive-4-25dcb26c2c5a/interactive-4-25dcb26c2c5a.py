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
        Output("status", ["Captain is content."])
    ])


@route
def hungrier(state: State) -> Fragment:
    state.hunger = state.hunger + 1
    if state.hunger < 3:
        mood = "Captain is content."
    elif state.hunger < 6:
        mood = "Captain is peckish."
    else:
        mood = "CAPTAIN REQUIRES SALMON. (" \
               + str(state.hunger) + ")"
    return Fragment([mood], target="#status")


start_server(State(0))
