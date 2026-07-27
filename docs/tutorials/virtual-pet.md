---
page_type: tutorial
title: 1. Care for a virtual pet
level: L1
audience: S
priority: P0
prereqs: [start/how-drafter-works]
symbols: []
outcome: Build a first interactive app where buttons change displayed data.
---

# 1. Care for a virtual pet

## What you'll build

You will build a virtual pet. The pet has a hunger level, an energy
level, and a mood that depends on both. Three buttons let you feed the
pet, play with it, and let it rest. Every click changes the pet's
numbers, and those numbers determine its mood.

## Try the finished app

Play with the finished version before building it. Feed the pet, play with
it until it gets tired, and figure out what makes its mood change:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int
    energy: int


def pet_mood(state: State) -> str:
    if state.hunger > 6:
        return "hungry"
    if state.energy < 3:
        return "sleepy"
    return "happy"


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hunger: " + str(state.hunger) + "\n",
        "Energy: " + str(state.energy) + "\n",
        "Mood: " + pet_mood(state) + "\n",
        Button("Feed", "feed"),
        Button("Play", "play"),
        Button("Rest", "rest")
    ])


@route
def feed(state: State) -> Page:
    state.hunger = state.hunger - 2
    if state.hunger < 0:
        state.hunger = 0
    return index(state)


@route
def play(state: State) -> Page:
    state.energy = state.energy - 3
    state.hunger = state.hunger + 2
    if state.energy < 0:
        state.energy = 0
    return index(state)


@route
def rest(state: State) -> Page:
    state.energy = state.energy + 3
    if state.energy > 10:
        state.energy = 10
    return index(state)


start_server(State(5, 5))
```

**Before building it, answer from playing**: what makes the mood say
"sleepy"? What fixes it?

## What you need

- The skills from [Start](../start/index.md): building a page, adding a
  button, running tests.
- One sitting.

## Step 1: The pet's data

Start with what the pet remembers: its hunger and its energy. There are
no buttons yet, only a page that shows the two values.

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int
    energy: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hunger: " + str(state.hunger) + "\n",
        "Energy: " + str(state.energy)
    ])


start_server(State(5, 5))
```

## Step 2: Feed the pet

Feeding reduces hunger by 2, but hunger should never go below zero. A
negative hunger value would not mean anything.

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int
    energy: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hunger: " + str(state.hunger) + "\n",
        "Energy: " + str(state.energy) + "\n",
        Button("Feed", "feed")
    ])


@route
def feed(state: State) -> Page:
    state.hunger = state.hunger - 2
    if state.hunger < 0:
        state.hunger = 0
    return index(state)


start_server(State(5, 5))
```

**Predict first**: starting from hunger 5, how many clicks of **Feed**
until hunger reaches 0? Click and check.

## Step 3: Play and rest

Next come two more actions. Playing costs energy and makes the pet
hungrier, while resting restores energy. Actions that push the numbers
in different directions are what make the pet feel alive.

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int
    energy: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hunger: " + str(state.hunger) + "\n",
        "Energy: " + str(state.energy) + "\n",
        Button("Feed", "feed"),
        Button("Play", "play"),
        Button("Rest", "rest")
    ])


@route
def feed(state: State) -> Page:
    state.hunger = state.hunger - 2
    if state.hunger < 0:
        state.hunger = 0
    return index(state)


@route
def play(state: State) -> Page:
    state.energy = state.energy - 3
    state.hunger = state.hunger + 2
    if state.energy < 0:
        state.energy = 0
    return index(state)


@route
def rest(state: State) -> Page:
    state.energy = state.energy + 3
    if state.energy > 10:
        state.energy = 10
    return index(state)


start_server(State(5, 5))
```

Each button's function has one job. It changes the numbers that its
action affects, keeps them in range, and then calls `index` to redraw
the page.

## Step 4: Give the pet a mood

The mood is not stored anywhere. It is **computed** from hunger and energy
each time the page is drawn. Computing the mood deserves its own
function, because `index` should not be crowded with mood rules. Add
tests while you are at it; the mood rules are exactly the kind of logic
that quietly breaks later.

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int
    energy: int


def pet_mood(state: State) -> str:
    if state.hunger > 6:
        return "hungry"
    if state.energy < 3:
        return "sleepy"
    return "happy"


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hunger: " + str(state.hunger) + "\n",
        "Energy: " + str(state.energy) + "\n",
        "Mood: " + pet_mood(state) + "\n",
        Button("Feed", "feed"),
        Button("Play", "play"),
        Button("Rest", "rest")
    ])


@route
def feed(state: State) -> Page:
    state.hunger = state.hunger - 2
    if state.hunger < 0:
        state.hunger = 0
    return index(state)


@route
def play(state: State) -> Page:
    state.energy = state.energy - 3
    state.hunger = state.hunger + 2
    if state.energy < 0:
        state.energy = 0
    return index(state)


@route
def rest(state: State) -> Page:
    state.energy = state.energy + 3
    if state.energy > 10:
        state.energy = 10
    return index(state)


assert_equal(pet_mood(State(8, 5)), "hungry")
assert_equal(pet_mood(State(2, 1)), "sleepy")
assert_state(feed(State(1, 5)), State(0, 5))
assert_has(index(State(5, 5)), "Mood: happy")

start_server(State(5, 5))
```

Notice that `pet_mood` has no `@route`. It is a plain helper function:
routes return pages, while helper functions return everything else. Read
the third test carefully; it checks the "never below zero" rule from
Step 2 by feeding a pet whose hunger is already 1.

## Step 5: Break it, watch a test catch it

On your own copy, change the first line of `feed` to **add** 2 instead of
subtracting. Run the app and open the debug panel's **Tests** tab. The
`assert_state` test fails and shows the difference: it expected hunger 0
and got hunger 3. Fix `feed` and watch the test pass again.

This is why the tests exist. You did not have to click anything to find
the bug; the tests checked the rules the moment the program started.

## Common problems

- **`payload.verification_failed` on `feed`, `play`, or `rest`**: the buttons in `index`
  refer to routes defined further down the file. Every name in a
  `Button(...)` must match a route function that exists. Check spelling first.
  Also make sure that the route function has `@route` above it, so that Drafter knows it is a route.
- **Hunger or energy goes negative or past 10**: one of your range checks
  is missing or checks the wrong direction. Compare with Step 3.
- **The mood never changes**: make sure the page shows
  `pet_mood(state)`, freshly computed, and that you did not store a mood
  value in `State`. A stored mood can go stale, but a computed mood
  cannot.
- **`State(...)` complains about arguments**: the order of the values in
  `State(5, 5)` must match the dataclass fields exactly.

## Name it

You have now used every idea from Start on a real app, plus two new ones:

- **State** is your app's memory: the pet's hunger and energy. Buttons
  change it, the page displays it, and reloading resets it. The full
  story is in [State](../concepts/state.md).
- **Routes** are the functions that return your pages and respond to
  your buttons: `index`, `feed`, `play`, and `rest`. How they connect is
  explained in [Routes and pages](../concepts/routes-and-pages.md).
- **Helper functions** like `pet_mood` keep routes short. Rules that
  compute something from state belong in helpers, where tests can reach
  them easily.

## Make it yours

1. Add a `happiness` field to `State`, changed by playing, and work it
   into `pet_mood`.
2. Add a "Treat" button: hunger down 1, happiness up, but energy down 1.
3. Make the pet's name part of `State` and show it in the page text.
4. Harder: if energy is 0, make `play` do nothing. Decide: should the
   page say why? Write a test for the new rule.

## Next steps

You unlocked two task pages:
[Remember a score or choice](../add/remember-things.md) generalizes what
you did with state, and
[Add and connect pages](../add/pages.md) is next when one page stops being
enough.

<div class="grid cards" markdown>

- **Next project: Build a story maker**

    ---

    The next project adds more pages, text boxes, and values that travel
    from one page to another.

    [Build a story maker](story-maker.md)

</div>
