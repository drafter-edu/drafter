from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Sound Effects Shelf"),
        "Victory: ",
        Melody([("C4", 0.5), ("E4", 0.5), ("G4", 0.5), ("C5", 1.5)],
               tempo=160),
        "\nOminous: ",
        Melody([("E3", 2), ("D#3", 2)], tempo=60,
               waveform="sawtooth", effects=[Reverb(amount=0.7)]),
        "\nDoorbell: ",
        Tone("E5", duration=300)
    ])


start_server(State())
