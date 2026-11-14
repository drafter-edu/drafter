from drafter import *
from dataclasses import dataclass
import random


@dataclass
class State:
    last_roll: int
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Dice game"),
        "You rolled: " + str(state.last_roll) + "\n",
        "Total so far: " + str(state.total) + "\n",
        Button("Roll", "roll")
    ])


def record_roll(state: State, value: int) -> Page:
    state.last_roll = value
    state.total = state.total + value
    return index(state)


@route
def roll(state: State) -> Page:
    return record_roll(state, random.randint(1, 6))


assert_state(record_roll(State(0, 0), 4), State(4, 4))
assert_state(record_roll(State(4, 4), 6), State(6, 10))
assert_has(record_roll(State(0, 0), 2), "You rolled: 2")

start_server(State(0, 0))
