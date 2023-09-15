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
        state.message,
        "Would you like to change the message?",
        TextBox("new_message", state.message),
        Button("Save", set_the_message)
    ])

@route
def set_the_message(state: State, new_message: str) -> Page:
    state.message = new_message
    return index(state)

start_server(State("The original message"))