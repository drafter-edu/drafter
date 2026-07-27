from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Python Tip of the Day"),
        Paragraph(
            "Calling ",
            InlineCode("state.treats + 1"),
            " computes a bigger number, but only ",
            InlineCode("state.treats = state.treats + 1"),
            " remembers it."
        )
    ])


start_server(State())
