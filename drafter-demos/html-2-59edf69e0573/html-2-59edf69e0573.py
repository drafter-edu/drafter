from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("From the old website"),
        RawHTML(
            "<blockquote cite='https://example.com'>"
            "<p>Domino remains the <em>only</em> cat to have"
            " been elected mayor of the living room.</p>"
            "</blockquote>"
        )
    ])


start_server(State())
