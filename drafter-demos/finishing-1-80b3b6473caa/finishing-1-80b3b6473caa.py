from drafter import *
from dataclasses import dataclass

set_website_title("The Compliment Machine")
set_website_style("sakura")
hide_debug_information()


@dataclass
class State:
    compliments: list[str]
    position: int


COMPLIMENTS = [
    "Your code is looking sharp today.",
    "Ada the corgi would sit for you.",
    "You debug with style."
]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Compliment Machine"),
        state.compliments[state.position] + "\n",
        Button("Another, please", "another")
    ])


@route
def another(state: State) -> Page:
    state.position = state.position + 1
    if state.position >= len(state.compliments):
        state.position = 0
    return index(state)


assert_equal(index(State(COMPLIMENTS, 0)),
             Page(State(COMPLIMENTS, 0), [
                 Header("The Compliment Machine"),
                 "Your code is looking sharp today.\n",
                 Button("Another, please", "another")
             ]))
assert_state(another(State(COMPLIMENTS, 2)), State(COMPLIMENTS, 0))

start_server(State(COMPLIMENTS, 0))
