from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    draft: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Notes"),
        TextArea("notes", state.draft, rows=4, on_input="keep"),
        "\n",
        Link("Wander off", "away")
    ])


@route
def keep(state: State, notes: str) -> Update:
    state.draft = notes
    return Update(state)


@route
def away(state: State) -> Page:
    return Page(state, [
        "You wandered off mid-thought.\n",
        Link("Return to your notes", "index")
    ])


start_server(State("Day 1: Domino has claimed the good chair."))
