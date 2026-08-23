"""
Demonstrates plain values (ints, floats, and booleans) used directly as
page content, without wrapping them in str().

A little dice-game score tracker that shows plain values working:
- directly in a Page's content list (int, float, bool)
- as a single bare content value (auto-wrapped into a list)
- nested inside layout components like Div and Row
- as items of a BulletedList
- inside a Table built from dataclasses with int/bool fields
- passed to styling helpers like bold() and italic(), which wrap
  them in a Text component
- in tests: Text(12) matches 12, and assert_has finds "12"
"""

import random
from dataclasses import dataclass, field

from drafter import *


@dataclass
class Roll:
    """One round of the game: the number rolled and whether it scored."""

    round_number: int
    rolled: int
    scored: bool


@dataclass
class State:
    score: int
    rounds_played: int
    on_a_streak: bool
    history: list[Roll] = field(default_factory=list)


@route
def index(state: State) -> Page:
    """The dashboard: numbers and booleans go straight into the content."""
    average = round(state.score / state.rounds_played, 2) if state.rounds_played else 0.0
    return Page(
        state,
        [
            Header("Dice Dash"),
            # ints, floats, and booleans can sit right next to strings:
            "Score:",
            state.score,
            LineBreak(),
            "Rounds played:",
            state.rounds_played,
            LineBreak(),
            "Average per round:",
            average,
            LineBreak(),
            "On a streak?",
            state.on_a_streak,
            LineBreak(),
            # Plain values also work nested inside layout components...
            Div(
                "Best possible round is",
                bold(6),  # ...and styling helpers wrap them in Text
                "points, worst is",
                italic(0),
            ),
            Button("Roll the die", roll),
            Button("See history", history),
        ],
    )


@route
def roll(state: State) -> Page:
    """Roll a six-sided die; 4 or higher scores the points rolled."""
    rolled = random.randint(1, 6)
    scored = rolled >= 4
    state.rounds_played += 1
    if scored:
        state.score += rolled
    if state.history:
        state.on_a_streak = scored and state.history[-1].scored
    else:
        state.on_a_streak = scored
    state.history.append(Roll(state.rounds_played, rolled, scored))
    return index(state)


@route
def history(state: State) -> Page:
    """Numbers work in list items and in table cells built from dataclasses."""
    rolls = [entry.rolled for entry in state.history]
    return Page(
        state,
        [
            Header("Roll History"),
            # BulletedList items can be plain numbers:
            "Every number rolled so far:",
            BulletedList(rolls),
            # Table cells render like page content, so the int and bool
            # fields of each Roll display without any conversion:
            Table(state.history),
            Button("Back", index),
        ],
    )


@route
def lucky_number(state: State) -> Page:
    """A single plain value is auto-wrapped into a content list."""
    return Page(state, 7)


# --- Tests -----------------------------------------------------------------

START = State(score=0, rounds_played=0, on_a_streak=False, history=[])

# The dashboard shows the plain values as text: 0 for the score and
# rounds, 0.0 for the average, False for the streak.
assert_has(index(START), "0.0")
assert_has(index(START), "False")

# Plain values compare directly in structural tests, and Text(6) is
# loosely equal to the plain 6 that bold() wrapped.
assert_equal(
    index(State(score=9, rounds_played=3, on_a_streak=True, history=[])),
    Page(
        State(score=9, rounds_played=3, on_a_streak=True, history=[]),
        [
            Header("Dice Dash"),
            "Score:",
            9,
            LineBreak(),
            "Rounds played:",
            3,
            LineBreak(),
            "Average per round:",
            3.0,
            LineBreak(),
            "On a streak?",
            True,
            LineBreak(),
            Div(
                "Best possible round is",
                Text(6),
                "points, worst is",
                Text(0),
            ),
            Button("Roll the die", roll),
            Button("See history", history),
        ],
    ),
)

# The history page puts ints in bullets and int/bool fields in table cells.
PLAYED = State(
    score=9,
    rounds_played=2,
    on_a_streak=True,
    history=[Roll(1, 4, True), Roll(2, 5, True)],
)
assert_has(history(PLAYED), BulletedList([4, 5]))
assert_has(history(PLAYED), Table([Roll(1, 4, True), Roll(2, 5, True)]))

# A single bare value works as the whole content argument.
assert_equal(lucky_number(START), Page(START, [7]))

start_server(START)
