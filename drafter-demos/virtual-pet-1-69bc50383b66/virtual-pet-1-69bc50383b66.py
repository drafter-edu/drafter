from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int
    energy: int


def pet_mood(state: State) -> str:
    if state.hunger > 6:
        return "hungry"
    if state.energy < 3:
        return "sleepy"
    return "happy"


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hunger: " + str(state.hunger) + "\n",
        "Energy: " + str(state.energy) + "\n",
        "Mood: " + pet_mood(state) + "\n",
        Button("Feed", "feed"),
        Button("Play", "play"),
        Button("Rest", "rest")
    ])


@route
def feed(state: State) -> Page:
    state.hunger = state.hunger - 2
    if state.hunger < 0:
        state.hunger = 0
    return index(state)


@route
def play(state: State) -> Page:
    state.energy = state.energy - 3
    state.hunger = state.hunger + 2
    if state.energy < 0:
        state.energy = 0
    return index(state)


@route
def rest(state: State) -> Page:
    state.energy = state.energy + 3
    if state.energy > 10:
        state.energy = 10
    return index(state)


start_server(State(5, 5))
