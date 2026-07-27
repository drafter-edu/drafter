from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clip: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Echo Cave"),
        "Record a shout, then choose your cave:\n",
        AudioRecorder("shout"),
        "\n",
        Button("Enter the cave", "cave")
    ])


@route
def cave(state: State, shout: Recording) -> Page:
    if shout.data_url is None:
        return Page(state, [
            "Record something first!\n",
            Button("Back", "index")
        ])
    state.clip = shout.data_url
    return Page(state, [
        Header("Choose your acoustics"),
        "Small cave: ",
        Sound(state.clip, effects=[Echo(delay=0.2, strength=0.3)]),
        "\nVast cavern: ",
        Sound(state.clip, effects=[Reverb(amount=0.8)]),
        "\nChipmunk ledge: ",
        Sound(state.clip, speed=1.8),
        "\n",
        Button("Record another", "index")
    ])


start_server(State(""))
