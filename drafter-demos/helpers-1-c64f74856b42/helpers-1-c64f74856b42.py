from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    warnings: int


@route
def index(state: State) -> Page:
    return Page(state, [
        bold("This line is bold.\n"),
        italic("This one is italic.\n"),
        change_color("This one is crimson.\n", "crimson"),
        bold(change_color("Warnings: " + str(state.warnings) + "\n", "darkorange")),
        Button("Add a warning", "warn")
    ])


@route
def warn(state: State) -> Page:
    state.warnings = state.warnings + 1
    return index(state)


start_server(State(0))
