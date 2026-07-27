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
    score: int


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
    question = state.questions[state.position]
    content = [
        Header("Question " + str(state.position + 1)),
        question.prompt + "\n"
    ]
    for option in question.options:
        content.append(Button(option, "check", [Argument("chosen", option)]))
        content.append("\n")
    return Page(state, content)


@route
def check(state: State, chosen: str) -> Page:
    question = state.questions[state.position]
    state.position = state.position + 1
    if chosen == question.answer:
        state.score = state.score + 1
        message = "Correct!"
    else:
        message = "Not quite. It was " + question.answer + "."
    if state.position < len(state.questions):
        return Page(state, [
            message + "\n",
            Button("Next question", "ask")
        ])
    return Page(state, [
        message + "\n",
        Button("See your results", "results")
    ])


@route
def results(state: State) -> Page:
    total = len(state.questions)
    if state.score == total:
        verdict = "Perfect. The pets are impressed."
    elif state.score >= total / 2:
        verdict = "Solid work."
    else:
        verdict = "The pets forgive you. Try again!"
    return Page(state, [
        Header("Results"),
        "You scored " + str(state.score) + " out of " + str(total) + ".\n",
        verdict + "\n",
        Button("Play again", "restart")
    ])


@route
def restart(state: State) -> Page:
    state.position = 0
    state.score = 0
    return index(state)


assert_state(check(State(QUESTIONS, 0, 0), "a cat"),
             State(QUESTIONS, 1, 1))
assert_state(check(State(QUESTIONS, 0, 0), "a dog"),
             State(QUESTIONS, 1, 0))
assert_has(results(State(QUESTIONS, 3, 3)), "You scored 3 out of 3.")

start_server(State(QUESTIONS, 0, 0))
