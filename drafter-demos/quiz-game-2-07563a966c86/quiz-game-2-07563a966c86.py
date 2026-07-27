from drafter import *
from dataclasses import dataclass


@dataclass
class Question:
    prompt: str
    options: list[str]
    answer: str


@dataclass
class State:
    questions: list[Question]
    position: int


QUESTIONS = [
    Question("What kind of animal is Captain?",
             ["a dog", "a cat", "a hamster"], "a cat"),
    Question("Which pet is a corgi?",
             ["Ada", "Babbage", "Domino"], "Ada"),
    Question("What color is Domino the cat?",
             ["black", "grey", "spotted"], "black")
]


@route
def index(state: State) -> Page:
    question = state.questions[state.position]
    return Page(state, [
        Header("The Pet Quiz"),
        "This quiz has " + str(len(state.questions)) + " questions.\n",
        "First up: " + question.prompt
    ])


start_server(State(QUESTIONS, 0))
