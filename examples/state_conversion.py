from dataclasses import dataclass

from drafter import *


@dataclass
class State:
    message: str


@route
def index(state: State) -> Page:
    return Page(state, ["The message is:", state.message])


start_server("The original message")
