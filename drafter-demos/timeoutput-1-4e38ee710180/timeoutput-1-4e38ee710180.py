from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adoption Fair"),
        Paragraph(
            "Meet the pets on ",
            TimeOutput("Saturday the 25th", datetime="2026-07-25"),
            " starting at ",
            TimeOutput("2 in the afternoon", datetime="14:00"),
            "."
        )
    ])


start_server(State())
