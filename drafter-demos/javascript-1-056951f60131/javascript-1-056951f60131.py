from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Browser Inspector"),
        Button("Inspect my browser", "inspect"),
        "\n" + state.report
    ])


@route
def inspect(state: State) -> Page:
    import js
    state.report = ("Your window is "
                    + str(js.window.innerWidth) + " by "
                    + str(js.window.innerHeight)
                    + " pixels, and your browser calls itself: "
                    + str(js.navigator.userAgent)[:60] + "...")
    return index(state)


start_server(State(""))
