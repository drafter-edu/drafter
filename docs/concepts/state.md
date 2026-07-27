---
page_type: concept
title: State
level: L2
audience: S
priority: P0
prereqs: [start/first-app]
symbols: []
outcome: Design and reason about application state.
---

# State

## In one sentence

State is the single dataclass holding everything your app remembers, and
it flows in a loop: into each route, onto each page, and into the next
route.

## The idea

Your app needs to remember things between clicks: a score, a name, a list
of items. In Drafter, all of it lives in one dataclass, which by
convention is always called `State`:

```python
@dataclass
class State:
    player_name: str
    score: int
    lives: int
```

`#!python start_server(State("Ada", 0, 3))` sets the starting values.
From then on, the state moves in a cycle:

1. A route receives the current state as its first parameter.
2. The route may **read** fields (to build the page) and **assign**
   fields (to record what happened).
3. The route returns a `Page(state, [...])`, which carries the state to
   the browser along with the content.
4. When the user clicks, the next route receives that same state, changes
   included.

Two important boundaries:

- **State resets on reload.** It lives in the browser's memory. Closing or
  reloading the tab starts over from the initial state, as
  [How Drafter works](../start/how-drafter-works.md) explains.
- **Fields should hold basic values.** Use `int`, `str`, `bool`, `float`,
  lists, and other dataclasses. A list of dataclasses is the right shape
  for collections: a to-do list, a quiz's questions, a shop's inventory.

## See it

Watch one field make the whole loop. The route reads `score` to build the
page and assigns `score` to record the click:

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        Button("Score a point", "add_point")
    ])


@route
def add_point(state: State) -> Page:
    state.score = state.score + 1
    return index(state)


assert_state(add_point(State(0)), State(1))

start_server(State(0))
```

Nested data works the same way. Here the state holds a list of dataclass
records, and the route loops over it to build the page:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    sound: str


@dataclass
class State:
    pets: list[Pet]


@route
def index(state: State) -> Page:
    lines = []
    for pet in state.pets:
        lines.append(pet.name + " says " + pet.sound + "!")
    return Page(state, [
        "The pets in the registry:",
        BulletedList(lines),
        Button("Add a duck", "add_duck")
    ])


@route
def add_duck(state: State) -> Page:
    state.pets.append(Pet("Duck", "quack"))
    return index(state)


start_server(State([Pet("Ada", "woof"), Pet("Captain", "meow")]))
```

## What this means for your code

- Use one `State` dataclass per app. If you are tempted to make a second
  one, you probably want a nested dataclass inside `State` instead.
- Design state by asking, for each page you sketch, "what changes here?"
  Whatever changes must be a field.
- Compute what you can instead of storing it. A pet's mood that depends on
  hunger belongs in a helper function, not in a field, so it can never go
  stale.
- Every route that reads or changes state takes `state` as its first
  parameter and passes it onward in `Page(state, [...])`.
- The debug panel's **Current** tab always shows your state; when
  behavior surprises you, look there first.

## Where people get confused

- **"I changed state but the page did not change"**: pages show state at
  the moment they were built. The change appears when a route runs and
  returns a fresh page. If it never appears, the route that should assign
  the field is not running or not assigning; check the debug panel's
  History tab.
- **"The back button broke my app"**: Drafter keeps a history of your
  pages and their states, and going back rewinds to the state that page
  had. That is usually what users expect, but it can surprise you while
  testing: your latest click is not "lost", you are looking at an earlier
  moment. The History tab shows exactly this timeline. Note that going
  backward means *replaying the route* that built that page, not *undoing
  the last route*. If you want to "undo" a click, you need to write a
  route that reverses it, such as one that subtracts a point or removes
  the last pet.
- **"Why not a global variable?"** Global variables are invisible to
  Drafter: they are not shown in the debugger, not carried in history, and
  not checked by `assert_state`. Everything the app remembers belongs in
  `State`, where the tools can see it. Avoid global variables unless you
  know exactly what you are doing; if you think you need one, you
  probably do not.
- **"Can I store a dictionary?"** Yes. Drafter supports dictionaries,
  sets, and other built-in types.

## Go deeper

- [Remember a score or choice](../add/remember-things.md) has recipes
  for common state patterns.
- [Show a collection of items](../add/show-a-collection.md) shows how
  to display lists of dataclasses on pages.
- [How Drafter works](../start/how-drafter-works.md) explains where
  state lives and why it resets.
- [Test a feature](../add/test-a-feature.md) covers `assert_state` and
  the related testing functions.
