from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    length: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Manuscript Weigher"),
        "Last manuscript: " + str(state.length) + " characters.\n",
        FileUpload("manuscript", accept=".txt"),
        "\n",
        Button("Weigh it", "weigh")
    ])


@route
def weigh(state: State, manuscript: str) -> Page:
    state.length = len(manuscript)
    return index(state)


start_server(State(0))
