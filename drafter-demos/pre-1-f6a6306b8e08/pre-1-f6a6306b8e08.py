from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    scoreboard = (
        "PET       TREATS   NAPS\n"
        "Ada           12      3\n"
        "Captain        2     14\n"
        "Domino         5      9"
    )
    return Page(state, [
        Header("Daily Report"),
        PreformattedText(scoreboard)
    ])


start_server(State())
