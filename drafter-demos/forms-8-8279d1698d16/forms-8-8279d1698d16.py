from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    when: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "The picnic is planned for: " + state.when + "\n",
        "Date:",
        DateInput("day"),
        "\nTime:",
        TimeInput("moment"),
        "\n",
        Button("Plan it", "plan")
    ])


@route
def plan(state: State, day: str, moment: str) -> Page:
    state.when = day + " at " + moment
    return index(state)


start_server(State("not planned yet"))
