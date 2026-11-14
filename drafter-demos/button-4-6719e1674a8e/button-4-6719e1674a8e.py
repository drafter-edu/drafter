from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    chores: list[str]


@route
def index(state: State) -> Page:
    content = [Header("Chores")]
    position = 0
    for chore in state.chores:
        content.append(chore + " ")
        content.append(Button("Delete", "delete", {"position": position}))
        content.append("\n")
        position = position + 1
    return Page(state, content)


@route
def delete(state: State, position: int) -> Page:
    state.chores.pop(position)
    return index(state)


start_server(State(["Walk Ada", "Brush Captain", "Feed Domino"]))
