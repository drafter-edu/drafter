from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Lost Cat Reporter"),
        "Spotted Captain? Share where you are.\n",
        CurrentLocation("where", show_coordinates=True),
        "\n",
        Button("Report sighting", "report"),
        "\n" + state.report
    ])


@route
def report(state: State, where: Location) -> Page:
    if where.status == "granted":
        state.report = ("Sighting recorded at "
                        + str(where.latitude) + ", "
                        + str(where.longitude))
    else:
        state.report = "No location shared: " + where.status
    return index(state)


start_server(State(""))
