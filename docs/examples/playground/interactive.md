---
page_type: playground
title: Interactive
level: L3
audience: S
priority: P2
prereqs: []
symbols: []
outcome: Tinker with events and partial updates.
---

# Interactive

Events, fragments, and timed behavior, each in a small demo made
for poking. The ideas behind all of them are in
[Live updates](../../concepts/live-updates.md).

## React to every keystroke

`on_input` calls a route as the visitor types, and the fragment
lands in the output region. Try changing the compliment rules, or
reacting to length instead of content:

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Pet Name Consultant"),
        "Propose a name:",
        TextBox("name", "", on_input="judge"),
        "\n",
        Output("verdict", ["The consultant awaits."])
    ])


@route
def judge(name: str) -> Fragment:
    if name == "":
        report = "The consultant awaits."
    elif len(name) > 12:
        report = "Distinguished, but hard to shout at the park."
    elif name.lower() == "captain":
        report = "Taken. The cat had it first."
    else:
        report = "'" + name + "' has promise."
    return Fragment([report], target="#verdict")


start_server()
```

## Save without saying so

`Update` changes state with no visible response, which is what
autosave should feel like. Type, leave, come back:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    draft: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Notes"),
        TextArea("notes", state.draft, rows=4, on_input="keep"),
        "\n",
        Link("Wander off", "away")
    ])


@route
def keep(state: State, notes: str) -> Update:
    state.draft = notes
    return Update(state)


@route
def away(state: State) -> Page:
    return Page(state, [
        "You wandered off mid-thought.\n",
        Link("Return to your notes", "index")
    ])


start_server(State("Day 1: Domino has claimed the good chair."))
```

## Race the clock

A persistent [Timer](../../reference/components/time/timer.md)
survives the re-render each click causes. Shorten the duration,
or award two points late in the countdown:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    caught: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Treat Toss"),
        "Catch treats for 6 seconds!\n",
        "Caught: " + str(state.caught) + "\n",
        Timer(6000, "times_up", persistent=True),
        "\n",
        Button("Catch one", "catch")
    ])


@route
def catch(state: State) -> Page:
    state.caught = state.caught + 1
    return index(state)


@route
def times_up(state: State) -> Page:
    return Page(state, [
        Header("Time!"),
        "Final haul: " + str(state.caught) + " treats."
    ])


start_server(State(0))
```

## Tick forever

A [Clock](../../reference/components/time/clock.md) drives the
page on a schedule; the fragment keeps the clock itself
untouched. Speed up the interval, or make hunger grow faster
than patience:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Tamagotchi Minute"),
        Clock(2000, "hungrier", show=False),
        Output("status", ["Captain is content."])
    ])


@route
def hungrier(state: State) -> Fragment:
    state.hunger = state.hunger + 1
    if state.hunger < 3:
        mood = "Captain is content."
    elif state.hunger < 6:
        mood = "Captain is peckish."
    else:
        mood = "CAPTAIN REQUIRES SALMON. (" \
               + str(state.hunger) + ")"
    return Fragment([mood], target="#status")


start_server(State(0))
```

## Keep going

- [Add live behavior](../../add/live-behavior.md): the recipes
  with explanations.
- [Make things happen over time](../../add/timers.md): the timed
  patterns in full.
