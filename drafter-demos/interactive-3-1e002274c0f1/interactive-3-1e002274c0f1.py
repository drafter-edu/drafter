from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    caught: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Treat Toss"),
        "Catch treats for 6 seconds!\n",
        "Caught: " + str(state.caught) + "\n",
        Timer(6000, "times_up", persistent=True),
        "\n",
        Button("Catch one", "catch")
    ])


@route
def catch(state: State) -> Page:
    state.caught = state.caught + 1
    return index(state)


@route
def times_up(state: State) -> Page:
    return Page(state, [
        Header("Time!"),
        "Final haul: " + str(state.caught) + " treats."
    ])


start_server(State(0))
