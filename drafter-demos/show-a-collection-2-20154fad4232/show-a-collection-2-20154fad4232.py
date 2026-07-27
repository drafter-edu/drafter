from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    kind: str
    sound: str


@dataclass
class State:
    pets: list[Pet]


@route
def index(state: State) -> Page:
    return Page(state, [
        "The pet registry:",
        Table(state.pets),
        Button("Register Domino", "add_domino")
    ])


@route
def add_domino(state: State) -> Page:
    state.pets.append(Pet("Domino", "cat", "meow"))
    return index(state)


assert_has(index(State([Pet("Ada", "corgi", "woof")])),
           Table([Pet("Ada", "corgi", "woof")]))

start_server(State([
    Pet("Ada", "corgi", "woof"),
    Pet("Babbage", "mutt", "woof"),
    Pet("Captain", "cat", "meow")
]))
