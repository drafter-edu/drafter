from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    replies: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Party invitation form.\n",
        "Your name:",
        TextBox("name"),
        "\nPick a meal:",
        SelectBox("meal", ["pizza", "salad", "soup"]),
        "\nBringing a guest?",
        CheckBox("guest"),
        "\n",
        Button("RSVP", "rsvp")
    ])


@route
def rsvp(state: State, name: str, meal: str, guest: bool) -> Page:
    state.replies = state.replies + 1
    lines = [
        name + " wants " + meal + ".\n"
    ]
    if guest:
        lines.append("They are bringing a guest.\n")
    lines.append("Replies so far: " + str(state.replies) + "\n")
    lines.append(Button("Next reply", "index"))
    return Page(state, lines)


assert_has(rsvp(State(0), "Ada", "pizza", False), "Ada wants pizza")
assert_has(rsvp(State(0), "Babbage", "soup", True), "bringing a guest")
assert_state(rsvp(State(4), "Domino", "salad", False), State(5))

start_server(State(0))
