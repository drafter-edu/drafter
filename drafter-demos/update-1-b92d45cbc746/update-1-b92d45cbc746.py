from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    draft: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Quiet Notebook"),
        "Write; the app remembers without reacting:",
        TextBox("text", state.draft, on_input="remember"),
        "\n",
        Button("Show what was saved", "reveal")
    ])


@route
def remember(state: State, text: str) -> Update:
    state.draft = text
    return Update(state)


@route
def reveal(state: State) -> Page:
    return Page(state, [
        "The saved draft: " + state.draft + "\n",
        Link("Back", "index")
    ])


start_server(State(""))
