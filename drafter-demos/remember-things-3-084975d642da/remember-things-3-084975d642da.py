from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int
    round_number: int


def new_game() -> State:
    return State(0, 1)


@route
def index(state: State) -> Page:
    return Page(state, [
        "Round " + str(state.round_number) + ", score " + str(state.score) + ".\n",
        Button("Win the round", "win"),
        Button("Start over", "reset")
    ])


@route
def win(state: State) -> Page:
    state.score = state.score + 10
    state.round_number = state.round_number + 1
    return index(state)


@route
def reset(state: State) -> Page:
    fresh = new_game()
    state.score = fresh.score
    state.round_number = fresh.round_number
    return index(state)


assert_state(reset(State(70, 8)), State(0, 1))

start_server(new_game())
