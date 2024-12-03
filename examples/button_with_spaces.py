from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    message: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Button("This is a test!", second_page),
        Button("Here's a different kind", second_page),
        Button("What's this button?", third_page, Argument("new_message", "This is the new message!"))
    ])


@route
def second_page(state: State) -> Page:
    return Page(state, [
        "Hello from the second page!"
    ])

@route
def third_page(state: State, new_message: str) -> Page:
    state.message = new_message
    return Page(state, [
        "The message is now:",
        state.message
    ])


start_server(State("Test"))