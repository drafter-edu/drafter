---
page_type: playground
title: Lists and tables
level: L2
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Tinker with data display.
---

# Lists and tables

Five small apps about showing collections. Edit anything; reloading
resets everything. The full story is
[Show a collection of items](../../add/show-a-collection.md).

## Bulleted and numbered

Same data, two components. Swap them and see which reads better.

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("The Plan"),
        "Ingredients (order does not matter):",
        BulletedList(["flour", "butter", "improbable optimism"]),
        "Steps (order very much matters):",
        NumberedList(["preheat", "mix", "regret nothing", "bake"])
    ])


start_server()
```

## A list that grows from state

The list component re-renders whatever the state holds. Add
something ridiculous.

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    sightings: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Backyard Sightings"),
        BulletedList(state.sightings),
        "Report a sighting:",
        TextBox("creature"),
        "\n",
        Button("Log it", "log")
    ])


@route
def log(state: State, creature: str) -> Page:
    state.sightings.append(creature)
    return index(state)


start_server(State(["one bold squirrel"]))
```

## Table: dataclasses become rows

Field names become the header row. Add a `weight_kg` field to the
dataclass and watch the table grow a column.

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    age: int


@route
def index() -> Page:
    return Page([
        Header("Residents"),
        Table([
            Pet("Ada", "corgi", 4),
            Pet("Babbage", "mutt", 6),
            Pet("Captain", "cat", 7),
            Pet("Domino", "cat", 2)
        ])
    ])


start_server()
```

## DefinitionList: labeled facts

One dataclass instance, rendered as term and definition pairs. Feed
it a different dataclass.

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class Recipe:
    name: str
    minutes: int
    difficulty: str


@route
def index() -> Page:
    return Page([
        Header("Tonight"),
        DefinitionList(Recipe("impossible pie", 45, "brave"))
    ])


start_server()
```

## ProgressBar and Meter: numbers as pictures

A `ProgressBar` shows completion; a `Meter` shows a measurement in a
range. Click and watch both move.

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    done: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Homework Machine"),
        "Problems done: " + str(state.done) + " of 10\n",
        ProgressBar(state.done, 10),
        "\nEnthusiasm remaining:\n",
        Meter(10 - state.done, 0, 10),
        "\n",
        Button("Do a problem", "work")
    ])


@route
def work(state: State) -> Page:
    if state.done < 10:
        state.done = state.done + 1
    return index(state)


start_server(State(3))
```

## Where next

- [Pet registry](../pet-registry.md): tables over real nested data.
- [To-do list](../todo-list.md): growing and shrinking list state.
