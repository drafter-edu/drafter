from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    greeting: str


@route
def index(state: State) -> Page:
    return Page(state, [
        state.greeting + "\n",
        "Your name:",
        TextBox("visitor"),
        "\n",
        Button("Say hello", "greet")
    ])


@route
def greet(state: State, visitor: str) -> Page:
    state.greeting = "Hello, " + visitor + "!"
    return index(state)


start_server(State("Hello, whoever you are!"))
