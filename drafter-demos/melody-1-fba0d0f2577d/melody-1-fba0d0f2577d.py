from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Dinner Bell"),
        "The song that summons every pet in the house:\n",
        Melody([("C4", 1), ("E4", 1), ("G4", 1), ("C5", 2),
                "rest", ("G4", 0.5), ("C5", 2.5)],
               tempo=140, waveform="triangle", controls=True)
    ])


start_server(State())
