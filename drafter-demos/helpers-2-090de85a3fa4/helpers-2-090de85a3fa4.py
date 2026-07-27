from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    accepted: bool


@route
def index(state: State) -> Page:
    notice = Div(
        bold("Field trip on Friday!\n"),
        "Bring a raincoat and a snack.\n"
    )
    return Page(state, [
        change_padding(change_border(notice, "2px solid steelblue"), "12px"),
        "\n",
        large_font(change_background_color(Button("Sounds fun!", "accept"), "lightgreen"))
    ])


@route
def accept(state: State) -> Page:
    state.accepted = True
    return Page(state, [
        "See you Friday!"
    ])


start_server(State(False))
