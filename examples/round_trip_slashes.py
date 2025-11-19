from drafter import *
from string import printable


@dataclass
class State:
    text: str
    label: str

@route
def index(state: State) -> Page:
    return Page(state, [
        "Type something",
        TextBox("text", state.text),
        Text(str(len(state.text))),
        Button(state.label, "next_page")
    ])

@route
def next_page(state: State, text: str) -> Page:
    state.text = text
    state.label = text

    return index(state)

start_server(State(printable, printable))