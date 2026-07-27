from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    packed: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        "Packed so far:",
        BulletedList(state.packed),
        RelatedCheckBox("supplies", "rope"),
        " rope\n",
        RelatedCheckBox("supplies", "lantern"),
        " lantern\n",
        RelatedCheckBox("supplies", "snacks"),
        " snacks\n",
        Button("Pack", "pack")
    ])


@route
def pack(state: State, supplies: list[str]) -> Page:
    state.packed = supplies
    return index(state)


start_server(State([]))
