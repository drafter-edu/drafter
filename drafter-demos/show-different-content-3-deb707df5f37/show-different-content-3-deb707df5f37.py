from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str


@dataclass
class State:
    pets: list[Pet]
    viewing: str


@route
def index(state: State) -> Page:
    content = [Header("The Registry")]
    for pet in state.pets:
        content.append(Button(pet.name, "show", [Argument("who", pet.name)]))
        content.append("\n")
    return Page(state, content)


@route
def show(state: State, who: str) -> Page:
    state.viewing = who
    found = "a mystery"
    for pet in state.pets:
        if pet.name == who:
            found = pet.species
    return Page(state, [
        Header(who),
        who + " is " + found + ".\n",
        Link("Back to the registry", "index")
    ])


start_server(State([
    Pet("Ada", "a corgi"),
    Pet("Babbage", "a small black mutt"),
    Pet("Captain", "a grey cat")
], ""))
