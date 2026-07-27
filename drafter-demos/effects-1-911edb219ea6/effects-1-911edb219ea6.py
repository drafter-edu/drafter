from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


NOTES = [("E4", 0.5), ("G4", 0.5), ("A4", 2)]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Effect Test Bench"),
        "Plain: ", Melody(NOTES),
        "\nHaunted: ", Melody(NOTES, effects=[Echo(delay=0.4),
                                              Reverb(amount=0.7)]),
        "\nThrough the wall: ", Melody(NOTES,
                                       effects=[Muffle(0.8)]),
        "\nBroken radio: ", Melody(NOTES,
                                   effects=[Distortion(0.6),
                                            Sharpen(0.6)])
    ])


start_server(State())
