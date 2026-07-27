from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    record: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Last entry: " + state.record + "\n",
        "Pet name:",
        TextBox("pet_name"),
        "\nAge:",
        TextBox("pet_age"),
        "\n",
        Button("Save", "save")
    ])


@route
def save(state: State, pet_name: str, pet_age: int) -> Page:
    state.record = pet_name + " (" + str(pet_age) + " years old)"
    return index(state)


start_server(State("none yet"))
