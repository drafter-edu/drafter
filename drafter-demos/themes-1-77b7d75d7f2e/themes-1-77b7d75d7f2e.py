from drafter import *
from dataclasses import dataclass

set_website_style("terminal")


@dataclass
class State:
    coins: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Coin Collector"),
        "Coins: " + str(state.coins) + "\n",
        Button("Grab a coin", "grab"),
        Button("Spend them all", "spend")
    ])


@route
def grab(state: State) -> Page:
    state.coins = state.coins + 1
    return index(state)


@route
def spend(state: State) -> Page:
    state.coins = 0
    return index(state)


start_server(State(0))
