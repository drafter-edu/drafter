---
page_type: playground
title: Basics
level: L1
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Tinker with hello, counter, and multi-page demos.
---

# Basics

Six tiny apps, growing one idea at a time. Edit anything; reloading
the page resets every demo.

## The smallest possible app

One route, one page, one string. Change the greeting.

```python drafter height=160
from drafter import *


@route
def index() -> Page:
    return Page(["Hello, world!"])


start_server()
```

Full story: [Build your first app](../../start/first-app.md).

## Text stays on one line unless you say otherwise

Strings sit side by side until a `"\n"` breaks the line. Move the
`"\n"`s around.

```python drafter height=180
from drafter import *


@route
def index() -> Page:
    return Page([
        "First. ",
        "Still the first line. ",
        "Now a break.\n",
        "Second line."
    ])


start_server()
```

## A button that changes state

The classic counter. Make it count by 10. Make it count down.

```python drafter height=200
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clicks: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Clicks so far: " + str(state.clicks) + "\n",
        Button("Click me", "add_one")
    ])


@route
def add_one(state: State) -> Page:
    state.clicks = state.clicks + 1
    return index(state)


start_server(State(0))
```

Full story: [State](../../concepts/state.md).

## The starting state is yours to choose

Same counter, different beginning. Start it at 100. Start it at -5.

```python drafter height=200
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clicks: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Clicks so far: " + str(state.clicks) + "\n",
        Button("Click me", "add_one")
    ])


@route
def add_one(state: State) -> Page:
    state.clicks = state.clicks + 1
    return index(state)


start_server(State(40))
```

## Two pages, connected

A `Button` and a `Link`, each naming a route. Add a third page.

```python drafter height=200
from drafter import *


@route
def index() -> Page:
    return Page([
        "The front porch.\n",
        Button("Go inside", "kitchen")
    ])


@route
def kitchen() -> Page:
    return Page([
        "The kitchen smells like toast.\n",
        Link("Back to the porch", "index")
    ])


start_server()
```

Full story: [Add and connect pages](../../add/pages.md).

## An emoji button

Button labels are just strings, and strings can be emoji. Change the
moods.

```python drafter height=200
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    mood: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Today's mood: " + state.mood + "\n",
        Button("😴", "sleepy"),
        Button("🎉", "party")
    ])


@route
def sleepy(state: State) -> Page:
    state.mood = "resting"
    return index(state)


@route
def party(state: State) -> Page:
    state.mood = "celebrating"
    return index(state)


start_server(State("undecided"))
```

## Where next

- [Build your first app](../../start/first-app.md) walks the counter
  properly.
- [Forms](forms.md) is the next collection: inputs instead of
  buttons.
