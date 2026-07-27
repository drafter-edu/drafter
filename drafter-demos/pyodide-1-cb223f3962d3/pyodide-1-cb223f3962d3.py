from drafter import *
from dataclasses import dataclass
import sys


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Where am I?"),
        "This Python is running on: " + sys.platform
    ])


start_server(State())
