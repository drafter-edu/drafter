from drafter import *
from dataclasses import dataclass

set_website_title("Corgi Cafe")
set_site_information(
    author="A. Student",
    description="Order snacks for very good dogs.",
    sources="",
    planning="",
    links=[]
)
hide_debug_information()


@dataclass
class State:
    snacks_served: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Corgi Cafe"),
        "Snacks served to Ada so far: " + str(state.snacks_served) + "\n",
        Button("Serve a snack", "serve")
    ])


@route
def serve(state: State) -> Page:
    state.snacks_served = state.snacks_served + 1
    return index(state)


assert_state(serve(State(0)), State(1))

start_server(State(0))
