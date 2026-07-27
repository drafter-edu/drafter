from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    favorite_food: str
    naps_per_day: int


@dataclass
class State:
    resident: Pet


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet of the Month"),
        DefinitionList(state.resident)
    ])


start_server(State(Pet("Captain", "grey cat", "salmon", 14)))
