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
    return Page(state, [
        Header("The Pet Quiz"),
        "Three questions. No pressure.\n",
        Button("Start the quiz", "ask")
    ])


@route
def ask(state: State) -> Page:
    if state.position >= len(state.questions):
        return Page(state, [
            "That was the last question!\n",
            Button("Back to the start", "restart")
        ])
    question = state.questions[state.position]
    return Page(state, [
        Header("Question " + str(state.position + 1)),
        question.prompt + "\n",
        BulletedList(question.options),
        Button("Skip", "skip")
    ])


@route
def skip(state: State) -> Page:
    state.position = state.position + 1
    return ask(state)


@route
def restart(state: State) -> Page:
    state.position = 0
    return index(state)


start_server(State(QUESTIONS, 0))
