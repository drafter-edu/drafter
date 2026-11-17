from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Roll Call"),
        Div("Ada the corgi", id="ada"),
        Div("Babbage the small black mutt", id="babbage"),
        Div("Captain the grey cat", id="captain"),
        Button("Find Babbage", "find_babbage")
    ])


@route
def find_babbage(state: State) -> Update:
    import js
    row = js.document.getElementById("babbage")
    row.style.background = "gold"
    return Update(state)


start_server(State())
