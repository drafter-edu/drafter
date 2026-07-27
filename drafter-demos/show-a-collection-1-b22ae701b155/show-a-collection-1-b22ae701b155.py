from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    chores: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        "Today's chores:",
        BulletedList(state.chores),
        Button("Add a chore", "add_chore"),
        Button("Finish one", "finish_chore")
    ])


@route
def add_chore(state: State) -> Page:
    state.chores.append("Walk the dogs")
    return index(state)


@route
def finish_chore(state: State) -> Page:
    if state.chores:
        state.chores.pop()
    return index(state)


start_server(State(["Feed the cats", "Water the plants"]))
