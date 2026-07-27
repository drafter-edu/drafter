from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Am I Home Yet?"),
        CurrentLocation("where", show_coordinates=True),
        "\n",
        Button("Check", "check"),
        "\n" + state.report
    ])


@route
def check(state: State, where: Location) -> Page:
    if where.status != "granted":
        state.report = "No reading (" + where.status + "), " \
                       "so: possibly home, possibly not."
    else:
        state.report = ("You are at " + str(where.latitude)
                        + ", " + str(where.longitude)
                        + ", accurate to about "
                        + str(where.accuracy) + " meters.")
    return index(state)


start_server(State(""))
