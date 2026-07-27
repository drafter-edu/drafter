from drafter import *
from dataclasses import dataclass

set_website_style("sakura")


@dataclass
class State:
    signups: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Corgi Fan Club"),
        "Members so far: " + str(state.signups) + "\n",
        "Ada approves of this club.\n",
        Button("Join the club", "join")
    ])


@route
def join(state: State) -> Page:
    state.signups = state.signups + 1
    return index(state)


start_server(State(0))
