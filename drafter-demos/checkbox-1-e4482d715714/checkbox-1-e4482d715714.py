from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    walked: bool
    fed: bool


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Babbage's Day"),
        "Walked: " + str(state.walked) + "\n",
        "Fed: " + str(state.fed) + "\n",
        CheckBox("walked_today", state.walked),
        " Took Babbage for a walk\n",
        CheckBox("fed_today", state.fed),
        " Fed Babbage\n",
        Button("Save", "save")
    ])


@route
def save(state: State, walked_today: bool, fed_today: bool) -> Page:
    state.walked = walked_today
    state.fed = fed_today
    return index(state)


start_server(State(False, False))
