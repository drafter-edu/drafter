from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    seconds_left: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Rocket Launch"),
        "Launching in " + str(state.seconds_left) + "...\n",
        Timer(10000, "launch", on_tick="tick",
              show=False, persistent=True)
    ])


@route
def tick(state: State, remaining: int) -> Page:
    state.seconds_left = remaining // 1000
    return index(state)


@route
def launch(state: State) -> Page:
    return Page(state, [Header("Liftoff!")])


start_server(State(10))
