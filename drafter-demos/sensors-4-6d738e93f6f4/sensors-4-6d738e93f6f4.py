from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    record_volume: float


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Wake the Dog"),
        "Babbage is asleep. Loudest attempt so far: "
        + str(round(state.record_volume, 2)) + "\n",
        Microphone("mic", threshold=0.4, cooldown=800,
                   on_loud="noise", visualize="bars"),
        "\n",
        Output("result", ["He sleeps on."])
    ])


@route
def noise(state: State, volume: float) -> Fragment:
    if volume > state.record_volume:
        state.record_volume = volume
        return Fragment(["A new record! He twitched an ear."],
                        target="#result")
    return Fragment(["Not your loudest. He sleeps on."],
                    target="#result")


start_server(State(0.0))
