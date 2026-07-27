from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Four Waveforms"),
        "Same pitch, four personalities:\n",
        "Smooth ", Tone("A4", waveform="sine"),
        " Buzzy ", Tone("A4", waveform="square"),
        " Mellow ", Tone("A4", waveform="triangle"),
        " Bright ", Tone("A4", waveform="sawtooth")
    ])


start_server(State())
