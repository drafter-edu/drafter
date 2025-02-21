from drafter import *
from dataclasses import dataclass


@dataclass
class Apples:
    message: str
    count: int


@route
def index(state: Apples) -> Page:
    return Page(state, [
        "The message is:",
        state.message,
        "There are",
        str(state.count),
        "apples."
    ])


start_server(Apples("The original message", 5))
