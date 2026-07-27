from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    age: int


@dataclass
class State:
    pets: list[Pet]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet Registry"),
        "There are " + str(len(state.pets)) + " pets registered.\n",
        Button("View the pets", "view_pets"),
        Button("Register a pet", "ask_new_pet")
    ])


@route
def view_pets(state: State) -> Page:
    return Page(state, [
        Header("All Pets"),
        Table(state.pets),
        Button("Back", "index")
    ])


@route
def ask_new_pet(state: State) -> Page:
    return Page(state, [
        Header("Register a pet"),
        "Name:",
        TextBox("name"),
        "\nSpecies:",
        SelectBox("species", ["dog", "cat", "capybara"]),
        "\nAge:",
        TextBox("age", 1),
        "\n",
        Button("Register", "save_pet"),
        Button("Cancel", "index")
    ])


@route
def save_pet(state: State, name: str, species: str, age: int) -> Page:
    state.pets.append(Pet(name, species, age))
    return index(state)


assert_state(save_pet(State([]), "Domino", "cat", 3),
             State([Pet("Domino", "cat", 3)]))
assert_has(view_pets(State([Pet("Ada", "dog", 4)])),
           Table([Pet("Ada", "dog", 4)]))

start_server(State([
    Pet("Ada", "dog", 4),
    Pet("Captain", "cat", 7)
]))
