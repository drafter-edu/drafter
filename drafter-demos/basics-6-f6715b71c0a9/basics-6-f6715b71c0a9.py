from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    mood: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Today's mood: " + state.mood + "\n",
        Button("😴", "sleepy"),
        Button("🎉", "party")
    ])


@route
def sleepy(state: State) -> Page:
    state.mood = "resting"
    return index(state)


@route
def party(state: State) -> Page:
    state.mood = "celebrating"
    return index(state)


start_server(State("undecided"))
