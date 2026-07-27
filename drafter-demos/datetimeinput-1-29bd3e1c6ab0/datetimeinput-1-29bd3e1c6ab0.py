from drafter import *
from dataclasses import dataclass
from datetime import datetime


@dataclass
class State:
    appointment: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Grooming Appointment"),
        "Babbage's next grooming: " + state.appointment + "\n",
        "Reschedule to:",
        DateTimeInput("moment", state.appointment),
        "\n",
        Button("Book it", "book")
    ])


@route
def book(state: State, moment: datetime) -> Page:
    state.appointment = moment.isoformat(timespec="minutes")
    return index(state)


start_server(State("2026-08-01T10:00"))
