from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    supplies: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Expedition Supplies"),
        BulletedList(state.supplies),
        "Add an item:",
        TextBox("item"),
        "\n",
        Button("Pack it", "pack")
    ])


@route
def pack(state: State, item: str) -> Page:
    state.supplies.append(item)
    return index(state)


start_server(State(["rope", "lantern"]))
