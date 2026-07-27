---
page_type: how-to
title: Remember a score or choice
level: L2
audience: S
priority: P0
prereqs: [start/first-app]
symbols: []
outcome: Keep information between clicks and pages.
---

# Remember a score or choice

## Goal

You want your app to keep a value, a score, a name, a chosen option,
between clicks and across pages.

## Before you start

You can build pages with buttons. Everything remembered lives in your
`State` dataclass, so "remember something new" always starts the same
way: **add a field**.

## The smallest version

To remember one more thing, add one more field, give it a starting value
in `start_server(...)`, and assign it in the routes that change it:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int
    best: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        "Best so far: " + str(state.best) + "\n",
        Button("Score a point", "add_point")
    ])


@route
def add_point(state: State) -> Page:
    state.score = state.score + 1
    if state.score > state.best:
        state.best = state.score
    return index(state)


assert_state(add_point(State(0, 0)), State(1, 1))
assert_state(add_point(State(2, 9)), State(3, 9))

start_server(State(0, 0))
```

`best` only ever grows, because only one route assigns it and that route
checks first. Deciding **which routes may change a field** is most of
state design.

## Recipe: save a choice, use it on another page

A value saved on one page is available on every page, because every route
receives the same state:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    difficulty: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Pick a difficulty:",
        SelectBox("choice", ["easy", "normal", "hard"], state.difficulty),
        "\n",
        Button("Save and continue", "save_difficulty")
    ])


@route
def save_difficulty(state: State, choice: str) -> Page:
    state.difficulty = choice
    return game(state)


@route
def game(state: State) -> Page:
    return Page(state, [
        "Now playing on " + state.difficulty + " mode.\n",
        Button("Change difficulty", "index")
    ])


assert_state(save_difficulty(State("easy"), "hard"), State("hard"))

start_server(State("normal"))
```

Two details worth copying: the `SelectBox` gets `state.difficulty` as its
starting value, so the form shows the current choice; and
`save_difficulty` does the saving, then hands off to `game` to build the
page, keeping each route to one job.

## Recipe: reset to the starting values

A reset is a route that assigns every field back to its starting value.
Write the starting values once, in a helper, so the reset and
`start_server` can never disagree:

```python drafter height=280
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
```

## What survives a reload

Nothing. State lives in the browser's memory, and reloading the tab
starts the app from `start_server(...)`'s values again. For course
projects that is normal and fine; say so on the page if your users might
be surprised. The full story is in
[How Drafter works](../start/how-drafter-works.md).

## Common problems

- **The value resets when you did not expect it**: you reloaded the tab,
  or a route assigns the field unconditionally. Check the debug panel's
  History tab to see which route changed it.
- **A field never changes**: no route assigns it, or the route that
  should is never reached. History again.
- **You added a field and old tests broke**: every `State(...)` call in
  your tests needs the new field's value too. The test failure lists the
  difference.
- **Two pages disagree about a value**: they cannot, if both read state.
  If one looks stale, it is showing text you built from an old value
  instead of reading `state` fresh in the route.

## Understand it

[State](../concepts/state.md): the state loop, what belongs in fields,
and what the back button does to them.

## See another example

The [virtual pet](../tutorials/virtual-pet.md): three fields, four
routes, and range rules.

## Look it up

[start_server](../reference/start-server.md) for initial state, and
[Testing functions](../reference/testing-functions.md) for
`assert_state`.

## Fix a problem

[State doesn't match the State class](../help/errors/state-mismatch.md).
