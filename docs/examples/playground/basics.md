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

This page collects six tiny apps, and each one adds a single new
idea. Edit anything you like. Reloading the page resets every demo.

## The smallest possible app

The whole app is a single route that returns a page containing one
string. Try changing the greeting.

```python drafter height=160
from drafter import *


@route
def index() -> Page:
    return Page(["Hello, world!"])


start_server()
```

The full story is in [Build your first app](../../start/first-app.md).

## Text stays on one line unless you say otherwise

Strings appear side by side on the same line until a `"\n"` starts
a new one. Move the `"\n"`s around and see how the lines change.

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

This is the classic counter app. See if you can make it count by 10,
or make it count down instead.

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

The full story is in [State](../../concepts/state.md).

## The starting state is yours to choose

This is the same counter with a different starting value. Change the
starting value to 100, or to -5.

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

This app connects two pages with a `Button` and a `Link`, each of
which names the route it leads to. Try adding a third page.

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

The full story is in [Add and connect pages](../../add/pages.md).

## An emoji button

Button labels are ordinary strings, and strings can contain emoji.
Try changing the moods.

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

- [Build your first app](../../start/first-app.md) walks through the
  counter step by step.
- [Forms](forms.md) is the next collection, where inputs take the
  place of buttons.
