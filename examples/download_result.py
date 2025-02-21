from drafter import *
from dataclasses import dataclass
import random


@dataclass
class State:
    rolls: list[str]





@route
def index(state: State) -> Page:
    return Page(state, [
        "Rolls:",
        Button("Add Roll", "add_roll"),
        Download("Download Rolls", "rolls.txt", "\n".join(state.rolls)),
        BulletedList(state.rolls)
    ])


@route
def add_roll(state: State) -> Page:
    state.rolls.append(str(random.randint(1, 6)))
    return index(state)

start_server(State(["1", "5", "3"]))