from drafter import *
from dataclasses import dataclass
from datetime import date


@dataclass
class State:
    checkup: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Vet Visit Planner"),
        "Ada's next checkup: " + state.checkup + "\n",
        "Pick a day:",
        DateInput("day", state.checkup),
        "\n",
        Button("Schedule", "schedule")
    ])


@route
def schedule(state: State, day: date) -> Page:
    state.checkup = day.isoformat()
    return index(state)


start_server(State("2026-08-15"))
