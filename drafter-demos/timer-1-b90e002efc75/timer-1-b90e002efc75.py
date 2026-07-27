from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clicks: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Speed Clicker"),
        "Pet Babbage as many times as you can in 5 seconds!\n",
        "Pets so far: " + str(state.clicks) + "\n",
        Timer(5000, "times_up", persistent=True),
        "\n",
        Button("Pet the dog", "pet")
    ])


@route
def pet(state: State) -> Page:
    state.clicks = state.clicks + 1
    return index(state)


@route
def times_up(state: State) -> Page:
    return Page(state, [
        Header("Time's up!"),
        "Babbage got " + str(state.clicks) + " pets. Good dog."
    ])


start_server(State(0))
