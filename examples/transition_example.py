from drafter import *


@dataclass
class State:
    value: int
    transition: str


DEFAULT_TRANSITION = "fade"

set_page_transition(DEFAULT_TRANSITION)


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            "This page demonstrates a transition between two pages.",
            "Click the button below to go to the next page.",
            SelectBox(
                "transition",
                ["fade", "white", "blue", "black", "#ff0000", "none"],
                state.transition,
            ),
            Button("Next Page", "next_page"),
        ],
    )


@route
def next_page(state: State, transition: str) -> Page:
    if state.transition != transition:
        state.transition = transition
        set_page_transition(transition)
    return Page(
        state,
        [
            "This is the next page.",
            "Click the button below to go back to the previous page.",
            Button("Previous Page", "index"),
        ],
    )


start_server(State(0, DEFAULT_TRANSITION))
