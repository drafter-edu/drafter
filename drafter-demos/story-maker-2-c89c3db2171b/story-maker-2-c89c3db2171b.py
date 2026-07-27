from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hero: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Who is the hero of the story?",
        TextBox("hero"),
        "\n",
        Button("Tell the story", "story")
    ])


@route
def story(state: State, hero: str) -> Page:
    state.hero = hero
    return Page(state, [
        "Once upon a time, there was " + state.hero + ".\n",
        Button("Start over", "index")
    ])


start_server(State(""))
