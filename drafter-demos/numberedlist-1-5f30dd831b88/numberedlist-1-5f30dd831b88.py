from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    queue: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Grooming Queue"),
        NumberedList(state.queue),
        Button("Groom the next pet", "next_pet")
    ])


@route
def next_pet(state: State) -> Page:
    if state.queue:
        state.queue.pop(0)
    return index(state)


start_server(State(["Ada", "Babbage", "Captain", "Domino"]))
