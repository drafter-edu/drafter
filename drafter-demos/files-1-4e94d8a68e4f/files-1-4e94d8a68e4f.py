from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    poem: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Poem Inspector"),
        "The current poem has " + str(len(state.poem)) + " characters.\n",
        "Upload a text file:",
        FileUpload("poem_file", accept=".txt"),
        "\n",
        Button("Inspect", "inspect")
    ])


@route
def inspect(state: State, poem_file: str) -> Page:
    state.poem = poem_file
    return Page(state, [
        "The file begins: " + state.poem[:40] + "\n",
        Link("Back", "index")
    ])


start_server(State(""))
