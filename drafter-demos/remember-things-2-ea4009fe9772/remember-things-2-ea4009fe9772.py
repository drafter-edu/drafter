from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    difficulty: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Pick a difficulty:",
        SelectBox("choice", ["easy", "normal", "hard"], state.difficulty),
        "\n",
        Button("Save and continue", "save_difficulty")
    ])


@route
def save_difficulty(state: State, choice: str) -> Page:
    state.difficulty = choice
    return game(state)


@route
def game(state: State) -> Page:
    return Page(state, [
        "Now playing on " + state.difficulty + " mode.\n",
        Button("Change difficulty", "index")
    ])


assert_state(save_difficulty(State("easy"), "hard"), State("hard"))

start_server(State("normal"))
