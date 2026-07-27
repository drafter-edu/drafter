from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        "Domino is a perfectly ordinary black cat.\n",
        Text("Except at 3 AM.", style_color="crimson",
             style_font_weight="bold")
    ])


start_server(State())
