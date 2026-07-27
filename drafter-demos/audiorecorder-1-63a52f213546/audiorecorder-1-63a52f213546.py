from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    last_message: str


@route
def index(state: State) -> Page:
    content = [
        Header("Voice Guestbook"),
        "Leave a message for the pets (10 seconds max):\n",
        AudioRecorder("message", max_duration=10000),
        "\n",
        Button("Leave message", "save")
    ]
    if state.last_message != "":
        content.append("\nThe latest message:\n")
        content.append(Sound(state.last_message))
    return Page(state, content)


@route
def save(state: State, message: Recording) -> Page:
    if message.data_url is None:
        return index(state)
    state.last_message = message.data_url
    return index(state)


start_server(State(""))
