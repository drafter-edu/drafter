from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("About Domino"),
        Paragraph(
            "Domino arrived on a Tuesday, inspected every room "
            "twice, and accepted the household by Thursday."
        ),
        Paragraph(
            "He has opinions about closed doors and none at all "
            "about the vacuum, which unsettles the other pets."
        )
    ])


start_server(State())
