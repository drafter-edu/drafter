from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    draft: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Autosaving Notepad"),
        TextArea("text", state.draft, rows=4, on_input="autosave"),
        "\n",
        Link("Leave and come back", "elsewhere")
    ])


@route
def autosave(state: State, text: str) -> Update:
    state.draft = text
    return Update(state)


@route
def elsewhere(state: State) -> Page:
    return Page(state, [
        "Off doing something else.\n",
        Link("Back to the notepad", "index")
    ])


start_server(State(""))
