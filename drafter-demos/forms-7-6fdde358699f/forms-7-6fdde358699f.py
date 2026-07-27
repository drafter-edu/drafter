from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    note: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "The fridge note says: " + state.note + "\n",
        "Rewrite it:",
        TextArea("new_note", state.note, rows=3),
        "\n",
        Button("Stick it on", "update")
    ])


@route
def update(state: State, new_note: str) -> Page:
    state.note = new_note
    return index(state)


start_server(State("buy more snacks"))
