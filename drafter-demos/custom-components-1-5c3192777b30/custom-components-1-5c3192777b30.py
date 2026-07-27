from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


def PetCard(name: str, species: str, motto: str) -> PageContent:
    return Div(
        Header(name, 3),
        Emphasis(species),
        Paragraph('"' + motto + '"'),
        style_border="2px solid #888",
        style_padding="8px",
        style_margin="8px"
    )


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Residents"),
        PetCard("Ada", "corgi", "Every walk is the best walk."),
        PetCard("Captain", "grey cat", "I was here first."),
        PetCard("Domino", "black cat", "You saw nothing.")
    ])


start_server(State())
