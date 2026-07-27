from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    answered: int


TOTAL_QUESTIONS = 8


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet Trivia"),
        "Question " + str(state.answered + 1) + " of "
        + str(TOTAL_QUESTIONS) + "\n",
        ProgressBar(state.answered, TOTAL_QUESTIONS),
        "\n",
        Button("Answer it", "answer")
    ])


@route
def answer(state: State) -> Page:
    if state.answered + 1 >= TOTAL_QUESTIONS:
        return Page(state, [Header("Quiz complete!")])
    state.answered = state.answered + 1
    return index(state)


start_server(State(0))
