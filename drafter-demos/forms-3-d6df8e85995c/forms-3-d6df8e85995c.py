from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    subscribed: bool


@route
def index(state: State) -> Page:
    return Page(state, [
        "Subscribed: " + str(state.subscribed) + "\n",
        CheckBox("wants_news", state.subscribed),
        " Send me the pigeon newsletter\n",
        Button("Save", "save")
    ])


@route
def save(state: State, wants_news: bool) -> Page:
    state.subscribed = wants_news
    return index(state)


start_server(State(False))
