from drafter import *
from dataclasses import dataclass

set_website_style("simple")


@dataclass
class State:
    lives: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Danger Zone"),
        bold(change_color("Lives remaining: " + str(state.lives), "crimson")),
        "\n",
        Button("Lose a life", "lose_life")
    ])


@route
def lose_life(state: State) -> Page:
    if state.lives > 0:
        state.lives = state.lives - 1
    return index(state)


start_server(State(3))
