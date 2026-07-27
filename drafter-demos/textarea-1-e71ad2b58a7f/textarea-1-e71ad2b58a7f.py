from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    entry: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Journal"),
        "Latest entry:\n",
        state.entry + "\n",
        "Write today's entry:",
        TextArea("new_entry", "", rows=4),
        "\n",
        Button("Save entry", "save")
    ])


@route
def save(state: State, new_entry: str) -> Page:
    state.entry = new_entry
    return index(state)


start_server(State("Day 1: Domino the cat refused to be observed."))
