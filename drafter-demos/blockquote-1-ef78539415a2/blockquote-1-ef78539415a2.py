from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("What Our Customers Say"),
        BlockQuote(None,
                   "Five stars. The corgi at the counter "
                   "approved my order personally."),
        "- A satisfied visitor"
    ])


start_server(State())
