---
page_type: how-to
title: Decide what to remember
level: L2
audience: S
priority: P1
prereqs: [your-project/sketch-the-pages]
symbols: []
outcome: Design state from the page sketches.
---

# Decide what to remember

## Goal

You want your `State` dataclass written down before coding, derived
from the sketches instead of invented on the fly.

## Before you start

You have [sketches](sketch-the-pages.md) with the changing parts
circled. The rule for this step is that **state is exactly the set
of circles**. Everything that changes must be remembered, and
everything remembered must appear (or matter) somewhere on a page.

## Step 1: List the circles

Go sketch by sketch and write every circled thing as a plain
phrase: "the list of entries", "which question is showing", "the
running total". Merge any duplicates: the total on the dashboard
and the total on the receipt are one fact shown in two places.

## Step 2: Give each a name and a type

Turn each phrase into a field with a type from the kit you know:

| The circle says | The field says |
| --------------- | -------------- |
| A number that changes | `score: int`, `total: float` |
| A yes/no situation | `logged_in: bool`, `finished: bool` |
| A piece of text | `player_name: str` |
| Which one of several | `position: int`, or a `str` name |
| A growing collection | `entries: list[Entry]` |
| A picture | `portrait: Picture` |

When each item in a collection has several parts of its own ("an
entry has a date, a distance, and a note"), you need a second,
smaller dataclass and a list of it. This is the pattern the
[pet registry](../examples/pet-registry.md) uses.

## Step 3: Write the dataclasses

The deliverable is real code, even though the app does not exist
yet:

```python
from dataclasses import dataclass


@dataclass
class Entry:
    date: str
    distance_km: float
    note: str


@dataclass
class State:
    entries: list[Entry]
    goal_km: float
```

Write down the starting value too, because every field needs
contents on day one: `State([], 100.0)`.

## Step 4: Interrogate the design

Three questions catch most state design problems before they cause
trouble:

- **Can it be derived?** The total distance is the sum of the
  entries, so storing the total *and* the entries invites them to
  disagree. Store the entries, and compute the total in a helper
  function.
  ([The virtual pet's mood](../tutorials/virtual-pet.md) taught
  this.)
- **Does anything never change?** A quiz's question list that never
  grows can still live in state (the
  [quiz game](../tutorials/quiz-game.md) keeps it there), but
  constant configuration might as well be a module-level constant.
- **Is anything missing?** Walk through a sketch path while
  narrating the state: "the user presses Save, so `entries` gains
  one..." If a click has nothing in the state to change, you
  missed a circle.

## Common problems

- **A field for every widget**: text boxes do not need fields of
  their own, because their values arrive as route parameters.
  State remembers what must *survive between* clicks, not what is
  in flight during one.
- **Twin facts**: `count` and a list whose length is the count, or
  a `logged_in` flag plus a `username` that means the same thing.
  Keep one, derive the other.
- **The kitchen-drawer dataclass**: fields added "just in case".
  Every field must point at a circle on a sketch. Delete the rest,
  and add fields later when a feature actually needs them.
- **Type dodging**: declaring `everything: str` only postpones
  type decisions, and they get harder the longer you wait. An age
  should be an `int` from day one.

## You are ready for the next step when

Your `State` (and any item dataclasses) are written, each field
traces to a circle, and the starting value is decided. Now
[build one working path](build-one-path.md).
