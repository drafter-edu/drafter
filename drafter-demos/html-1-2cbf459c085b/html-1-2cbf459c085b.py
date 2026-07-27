from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adoption Contract"),
        "I promise to give ",
        HtmlTag("u", "Babbage"),
        " belly rubs ",
        HtmlTag("u", "every single day"),
        "."
    ])


start_server(State())
