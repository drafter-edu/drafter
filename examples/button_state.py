from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    message: str

@route
def index(state: State) -> Page:
    return Page(state, [
        "The message is:",
        state.message,
        Button("Change the Message", change_message)
    ])

@route
def change_message(state: State) -> Page:
    state.message = "The new message!"
    return Page(state, [
        "Now the message is",
        state.message
    ])

start_server(State("The original message"))