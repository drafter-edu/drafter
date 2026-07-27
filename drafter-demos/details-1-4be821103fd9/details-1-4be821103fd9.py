from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Riddle"),
        "What has four legs, ignores you, and owns your house?\n",
        Details("Hint 1", "It is smaller than a dog.",
                group="hints"),
        Details("Hint 2", "It is currently on your keyboard.",
                group="hints"),
        Details("The answer", "A cat. Specifically, Captain.",
                group="hints")
    ])


start_server(State())
