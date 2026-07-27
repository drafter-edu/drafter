---
page_type: tutorial
title: 3. Make a quiz game
level: L2
audience: S
priority: P1
prereqs: [tutorials/story-maker]
symbols: []
outcome: Build a data-driven branching app from a list of dataclasses.
---

# 3. Make a quiz game

## What you'll build

A quiz about the pets. Three questions live in a list; one route shows
whichever question is next; each answer is a button; right and wrong
answers get different responses; and a score builds toward a results
page that changes with how you did.

The new idea is that the *data drives the pages*. In the story maker,
every page had its own route. Here, one `ask` route serves every
question, because the questions are values in a list and the app just
keeps track of which one you are on.

## Try the finished app

Take the quiz once honestly and once wrongly, and watch what changes:

```python drafter height=400
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


start_server(State(QUESTIONS, 0, 0))
```

## What you need

You have finished [the story maker](story-maker.md): you can build
forms whose values arrive as route parameters. Budget one or two
sittings; the quiz grows in four steps, each runnable.

## Step 1: The questions are data

A quiz question has three parts: the prompt, the options, and the
right answer. That is a dataclass. The whole quiz is a list of them,
and the state carries the list plus a `position`: which question is
next.

```python drafter height=280
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
```

**What this means**: `state.questions[state.position]` is the whole
trick of this project. The page does not know anything about pets; it
shows whatever question the position points at.

**Predict first**: change the last line to
`start_server(State(QUESTIONS, 2))`. What will the page show? Run it
and check. Then predict what `State(QUESTIONS, 3)` will do before you
try it. (It breaks: there is no question 3. Read the error, then put
the 0 back. Step 3 will make running out of questions mean something.)

## Step 2: One route, every question

Rename the question display into its own `ask` route, show the options
with a `BulletedList`, and add a Skip button that moves the position
forward. One route now serves every question.

```python drafter height=320
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
```

**What this means**: `ask` now has a branch. If the position has run
off the end of the list, it shows an ending instead of a question.
One route, several completely different pages: which one you get
depends on state. Drafter calls pages like this *dynamic*, and you
will meet the idea again everywhere.

**Predict first**: add a fourth `Question(...)` to the list. How many
skips until the ending page? Check.

## Step 3: Answers are buttons

Skip was a placeholder. Real quizzes answer. Replace the
`BulletedList` with one `Button` per option, built in a loop, and give
every button the same target: a new `check` route. The button carries
which option it was via an `Argument`.

Replace `ask` and `skip` with:

```python
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
        Button("Back to the start", "restart")
    ])
```

Here is the whole program at this stage, runnable:

```python drafter height=360
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
        Button("Back to the start", "restart")
    ])


@route
def restart(state: State) -> Page:
    state.position = 0
    return index(state)


start_server(State(QUESTIONS, 0))
```

**What this means**: every answer button points at the same `check`
route; the `Argument("chosen", option)` is what makes them different.
When a button is clicked, its argument fills `check`'s `chosen`
parameter, exactly the way a text box's contents filled a parameter in
the story maker. Then `check` compares `chosen` against the right
answer and branches.

**Predict first**: in `check`, what happens to the position when the
answer is wrong? Is that what a quiz should do? (It moves forward
either way; a question is asked once, right or wrong.)

## Step 4: Keep score, vary the ending

Add a `score` field, count correct answers in `check`, and replace the
plain ending with a `results` route whose verdict depends on the
score. The finished app at the top of the page is exactly this step;
its last lines before `start_server` are three tests:

```python
assert_state(check(State(QUESTIONS, 0, 0), "a cat"),
             State(QUESTIONS, 1, 1))
assert_state(check(State(QUESTIONS, 0, 0), "a dog"),
             State(QUESTIONS, 1, 0))
assert_has(results(State(QUESTIONS, 3, 3)), "You scored 3 out of 3.")
```

Add them to your copy, above `start_server(...)`. The first two pin
down the scoring rule from both sides: a right answer moves the
position and the score, a wrong answer moves only the position. The
third checks the results page for a perfect run.

**Break it on purpose**: change `check` to add 2 points per correct
answer, run the app, and open the debug panel's Tests tab. The first
test fails and shows the state it expected against the state it got.
Fix it and watch the tests go green.

## Common problems

- **`IndexError` (list position out of range)**: `state.position` ran
  past the end of `state.questions`. It usually means a route indexed
  the list without the `position < len(...)` guard, or moved the
  position twice for one answer.
- **The same question repeats forever**: nothing moves
  `state.position` forward. It should advance exactly once, inside
  `check`.
- **Every answer says correct**: compare `chosen == question.answer`
  against the question *before* moving the position, and check that
  each option string matches its `answer` exactly, including case.
- **A `missing parameter` error on `check`**: the answer buttons must
  each carry `[Argument("chosen", option)]`; without it, nothing fills
  the `chosen` parameter.
- **`Play again` shows question 4 of 3**: `restart` must reset both
  `position` and `score` to 0.

## Name it

Two ideas got names while you built this:

- **Dynamic pages**: one route that renders differently depending on
  state and arguments. `ask` shows any question; `results` changes
  its verdict; `check` branches on right and wrong. The full idea is
  [Dynamic pages](../concepts/dynamic-pages.md).
- **Arguments**: extra values a button carries to its route, filling
  parameters by name, just like form fields do. Details on the
  [Argument](../reference/components/actions/argument.md) reference
  page.

And one older idea grew: your state now contains a **list of
dataclasses**. The quiz's whole personality lives in `QUESTIONS`;
change the data and the same code runs a different quiz.

## Make it yours

1. Write three more questions about anything you like. Notice you
   never touch the routes.
2. Show the running score on every question page.
3. Add a `wrong: list[str]` field collecting the prompts of missed
   questions, and show them on the results page with a
   `BulletedList`.
4. Harder: a branching story is this same program wearing a costume.
   Each "question" is a scene, each "option" leads somewhere, and
   instead of a score you track which scene comes next. Sketch the
   `Scene` dataclass and try it.

## Next steps

You unlocked two task pages:
[Show a collection of items](../add/show-a-collection.md) for
displaying lists like your questions, and
[Show different content](../add/show-different-content.md) for
dynamic pages beyond quizzes.

<div class="grid cards" markdown>

- **Next project: Finish and test an app**

    ---

    Take the quiz (or any app) from "works" to "finished": frozen
    regression tests, a theme, and production settings.

    [Finish and test an app](finishing.md)

</div>
