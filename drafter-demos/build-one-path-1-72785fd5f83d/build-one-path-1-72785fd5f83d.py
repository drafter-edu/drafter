from drafter import *
from dataclasses import dataclass


@dataclass
class Entry:
    date: str
    distance_km: float
    note: str


@dataclass
class State:
    entries: list[Entry]
    goal_km: float


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Trail Tracker"),
        "Entries so far: " + str(len(state.entries))
    ])


start_server(State([], 100.0))
