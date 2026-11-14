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

Your state holds a list of things, such as a to-do list, a team roster,
or an inventory, and you want the page to show every item, however many
there are.

## Before you start

You can keep values in state. One pattern runs through this page: the
collection is a **list in state**, and the page rebuilds its display
from that list on every visit, so adding or removing items requires no
extra display code.

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

## Recipe: a button for each item

To let the visitor remove or edit one particular item, give every row
its own buttons. Each button carries an `Argument` that holds the
item's position in the list, and the route receives that position as a
parameter with the same name.

```python drafter height=360
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    chores: list[str]


def chore_rows(chores: list[str]) -> list:
    rows = []
    position = 0
    for chore in chores:
        rows.append(chore + " ")
        rows.append(Button("Rename", "edit_chore", Argument("position", position)))
        rows.append(Button("Done", "finish_chore", Argument("position", position)))
        rows.append("\n")
        position = position + 1
    return rows


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Today's chores")
    ] + chore_rows(state.chores))


@route
def finish_chore(state: State, position: int) -> Page:
    state.chores.pop(position)
    return index(state)


@route
def edit_chore(state: State, position: int) -> Page:
    return Page(state, [
        "Rename this chore:",
        TextBox("new_name", state.chores[position]),
        "\n",
        Button("Save", "save_chore", Argument("position", position)),
        Button("Cancel", "index")
    ])


@route
def save_chore(state: State, position: int, new_name: str) -> Page:
    state.chores[position] = new_name
    return index(state)


assert_state(finish_chore(State(["Feed the cats", "Walk the dogs"]), 0),
             State(["Walk the dogs"]))
assert_state(save_chore(State(["Feed the cats", "Walk the dogs"]), 1, "Walk Ada"),
             State(["Feed the cats", "Walk Ada"]))

start_server(State(["Feed the cats", "Walk the dogs", "Water the plants"]))
```

The loop in `chore_rows` counts positions as it goes. The first
chore's buttons carry `Argument("position", 0)`, the second chore's
buttons carry `Argument("position", 1)`, and so on. Every "Done" button
goes to the same `finish_chore` route, and the argument is how that
route learns which button was pressed.

Renaming takes two routes. The `edit_chore` route shows a text box
that starts with the chore's current name. Its Save button passes the
same position along to `save_chore`, which replaces that one item. The
position has to travel through the edit page because a parameter lasts
for one route call only.

The Cancel button returns to the list without saving. The text box's
value is still sent with that click, and `index` has no parameter for
it, so the debug panel lists a warning about
[a form field with no matching parameter](../help/errors/missing-parameter.md#a-related-warning-a-form-field-with-no-matching-parameter).
That warning is expected here and does not affect the page.

## Recipe: show only the items that match

A search box is a filter. The page shows the items that contain what
the visitor typed and leaves the rest out. Keep the full list in state,
keep the search text in state as well, and build the shorter list each
time the page is displayed.

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pets: list[str]
    search_text: str


def matching_pets(pets: list[str], search_text: str) -> list[str]:
    matches = []
    for pet in pets:
        if search_text.lower() in pet.lower():
            matches.append(pet)
    return matches


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet finder"),
        "Show pets whose description contains:",
        TextBox("search_text", state.search_text),
        Button("Search", "search"),
        "\n",
        BulletedList(matching_pets(state.pets, state.search_text))
    ])


@route
def search(state: State, search_text: str) -> Page:
    state.search_text = search_text
    return index(state)


assert_equal(matching_pets(["Ada the corgi", "Captain the grey cat"], "CAT"),
             ["Captain the grey cat"])
assert_equal(matching_pets(["Ada the corgi", "Captain the grey cat"], ""),
             ["Ada the corgi", "Captain the grey cat"])

start_server(State([
    "Ada the corgi",
    "Babbage the small black mutt",
    "Captain the grey cat",
    "Domino the black cat"
], ""))
```

The `matching_pets` function never changes `state.pets`. It builds a
new list for display, so clearing the search box and pressing Search
brings every pet back. Comparing lowercase copies with `.lower()` makes
the search ignore capital letters. An empty search box matches every
pet, because every string contains the empty string.

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

This example also shows how to add items from real input: the
`TextBox` value arrives as a parameter, and the route appends it to the
list.

## Common problems

- **The list displays oddly, with items run together**: you put the raw
  list into the content directly. Wrap it in a component:
  `BulletedList(state.chores)`, not `state.chores`.
- **An error when removing an item**: the list was empty. Guard with
  `if state.chores:` before `pop`, as the first recipe does.
- **Every row's button changes the same item**: the buttons do not
  carry different arguments. Check that the `Argument` value changes
  inside the loop, as `position` does in the button-for-each-item
  recipe.
- **The table's columns look wrong**: `Table` reads column names from
  the dataclass fields. If a row is not that dataclass, or the list
  mixes types, rows will not line up.
- **New items do not appear**: the route changed a copy, not the state's
  list. Use `state.pets.append(...)` on the state's own list.

## Understand it

[State](../concepts/state.md) covers nested dataclasses and lists as
your app's memory.

## See another example

The [pet registry](../examples/pet-registry.md) adds and views records
with a table, and the [to-do list](../examples/todo-list.md) shows
adding and removing items.

## Look it up

[BulletedList](../reference/components/lists/bulletedlist.md),
[NumberedList](../reference/components/lists/numberedlist.md),
[Table](../reference/components/data/table.md), and
[Argument](../reference/components/actions/argument.md).

## Fix a problem

[State doesn't match the State class](../help/errors/state-mismatch.md),
and [Page content must be a list](../help/errors/page-content-invalid.md)
for content-shape mistakes.
