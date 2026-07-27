from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    toppings: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Sundae Builder"),
        "Current toppings:",
        BulletedList(state.toppings),
        RelatedCheckBox("picks", "sprinkles"),
        " sprinkles\n",
        RelatedCheckBox("picks", "cherries"),
        " cherries\n",
        RelatedCheckBox("picks", "regret"),
        " regret\n",
        Button("Build it", "build")
    ])


@route
def build(state: State, picks: list[str]) -> Page:
    state.toppings = picks
    return index(state)


start_server(State([]))
