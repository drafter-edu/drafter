---
page_type: how-to
title: Show a collection of items
level: L2
audience: S
priority: P0
prereqs: [add/remember-things]
symbols: []
outcome: Display lists and tables from state.
---

# Show a collection of items

## Goal

Your state holds a list of things, a to-do list, a team roster, an
inventory, and you want the page to show all of them, however many there
are.

## Before you start

You can keep values in state. The pattern here: the collection is a
**list in state**, and the page builds its display from that list fresh
each time, so adding or removing items just works.

## The smallest version

`BulletedList` turns a Python list into a bulleted list on the page.
Grow the list in a route and the display grows with it:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    chores: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        "Today's chores:",
        BulletedList(state.chores),
        Button("Add a chore", "add_chore"),
        Button("Finish one", "finish_chore")
    ])


@route
def add_chore(state: State) -> Page:
    state.chores.append("Walk the dogs")
    return index(state)


@route
def finish_chore(state: State) -> Page:
    if state.chores:
        state.chores.pop()
    return index(state)


start_server(State(["Feed the cats", "Water the plants"]))
```

`NumberedList` works the same way when order matters. Note the guard in
`finish_chore`: removing from an empty list is an error, so check first.

## Recipe: a table from a list of dataclasses

When each item has several parts, make the item a dataclass and the
collection a list of them. `Table` turns that list into rows, with the
field names as column headers:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    kind: str
    sound: str


@dataclass
class State:
    pets: list[Pet]


@route
def index(state: State) -> Page:
    return Page(state, [
        "The pet registry:",
        Table(state.pets),
        Button("Register Domino", "add_domino")
    ])


@route
def add_domino(state: State) -> Page:
    state.pets.append(Pet("Domino", "cat", "meow"))
    return index(state)


assert_has(index(State([Pet("Ada", "corgi", "woof")])),
           Table([Pet("Ada", "corgi", "woof")]))

start_server(State([
    Pet("Ada", "corgi", "woof"),
    Pet("Babbage", "mutt", "woof"),
    Pet("Captain", "cat", "meow")
]))
```

The test's needle is a whole component: it checks the page contains that
exact one-pet table. (Text needles like `"Ada"` search the page's text,
which does not reach inside a table's rows.)

## Recipe: build the display with a loop

When neither a plain list nor a table fits, build the content yourself.
Loop over the collection, make a piece of content per item, and put the
pieces in the page's list. A helper function keeps the route readable:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class Player:
    name: str
    score: int


@dataclass
class State:
    players: list[Player]


def scoreboard(players: list[Player]) -> list:
    lines = []
    for player in players:
        lines.append(player.name + ": " + str(player.score) + " points\n")
    return lines


@route
def index(state: State) -> Page:
    return Page(state, [
        "Scoreboard:\n"
    ] + scoreboard(state.players) + [
        Button("Everyone scores", "all_score")
    ])


@route
def all_score(state: State) -> Page:
    for player in state.players:
        player.score = player.score + 1
    return index(state)


start_server(State([Player("Red team", 3), Player("Blue team", 5)]))
```

## Recipe: handle the empty case

A collection page should still make sense with nothing in it. Check for
the empty list and say something helpful instead of showing a blank
space:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    wishes: list[str]


@route
def index(state: State) -> Page:
    if state.wishes:
        display = BulletedList(state.wishes)
    else:
        display = "Your wishlist is empty. Add something!"
    return Page(state, [
        "Wishlist:\n",
        display,
        "\n",
        TextBox("wish"),
        "\n",
        Button("Add to wishlist", "add_wish")
    ])


@route
def add_wish(state: State, wish: str) -> Page:
    state.wishes.append(wish)
    return index(state)


assert_has(index(State([])), "empty")

start_server(State([]))
```

This one also shows the add-an-item pattern with real input: the
`TextBox` value arrives as a parameter, and the route appends it.

## Common problems

- **The page shows the list weirdly, all run together**: you put the raw
  list into the content directly. Wrap it: `BulletedList(state.chores)`,
  not `state.chores`.
- **An error when removing an item**: the list was empty. Guard with
  `if state.chores:` before `pop`, as the first recipe does.
- **The table's columns look wrong**: `Table` reads column names from
  the dataclass fields. If a row is not that dataclass, or the list
  mixes types, rows will not line up.
- **New items do not appear**: the route changed a copy, not the state's
  list. Use `state.pets.append(...)` on the state's own list.

## Understand it

[State](../concepts/state.md): nested dataclasses and lists as your
app's memory.

## See another example

[Pet registry](../examples/pet-registry.md): add and view records with a
table, and the [to-do list](../examples/todo-list.md) for add and remove.

## Look it up

[BulletedList](../reference/components/lists/bulletedlist.md),
[NumberedList](../reference/components/lists/numberedlist.md), and
[Table](../reference/components/data/table.md).

## Fix a problem

[State doesn't match the State class](../help/errors/state-mismatch.md),
and [Page content must be a list](../help/errors/page-content-invalid.md)
for content-shape mistakes.
