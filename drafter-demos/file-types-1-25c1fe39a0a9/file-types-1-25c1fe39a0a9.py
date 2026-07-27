from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Poem Collector"),
        state.report + "\n",
        FileUpload("poem"),
        "\n",
        Button("Submit poem", "receive")
    ])


@route
def receive(state: State, poem: DrafterTextFile) -> Page:
    lines = poem.content.split("\n")
    state.report = (poem.filename + " received: "
                    + str(len(lines)) + " lines, "
                    + str(poem.size) + " bytes.")
    return index(state)


start_server(State("No poems yet."))
