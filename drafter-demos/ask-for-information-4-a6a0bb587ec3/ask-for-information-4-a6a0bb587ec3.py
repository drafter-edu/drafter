from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    review: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Review our arcade:",
        "\n",
        TextArea("review", state.review),
        "\n",
        Button("Submit review", "thank_you")
    ])


@route
def thank_you(state: State, review: str) -> Page:
    state.review = review
    return Page(state, [
        "Thanks! You wrote:\n",
        state.review + "\n",
        Button("Edit your review", "index")
    ])


start_server(State(""))
