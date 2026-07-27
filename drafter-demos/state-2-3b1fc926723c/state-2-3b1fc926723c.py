from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    sound: str


@dataclass
class State:
    pets: list[Pet]


@route
def index(state: State) -> Page:
    lines = []
    for pet in state.pets:
        lines.append(pet.name + " says " + pet.sound + "!")
    return Page(state, [
        "The pets in the registry:",
        BulletedList(lines),
        Button("Add a duck", "add_duck")
    ])


@route
def add_duck(state: State) -> Page:
    state.pets.append(Pet("Duck", "quack"))
    return index(state)


start_server(State([Pet("Ada", "woof"), Pet("Captain", "meow")]))
