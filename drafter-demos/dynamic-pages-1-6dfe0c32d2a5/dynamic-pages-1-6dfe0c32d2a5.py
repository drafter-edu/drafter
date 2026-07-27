from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    fed: bool


@dataclass
class State:
    pets: list[Pet]


@route
def index(state: State) -> Page:
    content = [Header("The Pet Hotel")]
    for pet in state.pets:
        if pet.fed:
            content.append(pet.name + " is fed and happy.\n")
        else:
            content.append(pet.name + " is hungry! ")
            content.append(Button("Feed " + pet.name, "feed",
                                  [Argument("pet_name", pet.name)]))
            content.append("\n")
    return Page(state, content)


@route
def feed(state: State, pet_name: str) -> Page:
    for pet in state.pets:
        if pet.name == pet_name:
            pet.fed = True
    return index(state)


assert_state(
    feed(State([Pet("Ada", "corgi", False)]), "Ada"),
    State([Pet("Ada", "corgi", True)]))

start_server(State([
    Pet("Ada", "corgi", False),
    Pet("Captain", "cat", False),
    Pet("Domino", "cat", True)
]))
