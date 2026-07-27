---
page_type: how-to
title: Show different content
level: L3
audience: S
priority: P1
prereqs: [add/remember-things]
symbols: []
outcome: Make one page respond to state and choices.
---

# Show different content

## Goal

You want one page to say different things in different situations: a
greeting that changes once the visitor has a name, a warning that
appears only when something is wrong, one detail page that works for
every item in a list.

## Before you start

You can build a page that shows values from state. When you finish
this page, your routes will branch, and several buttons will share
one route politely.

## The smallest version

An `if` inside the route. The route runs fresh on every visit, so the
branch is re-decided every time:

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    water_level: int


@route
def index(state: State) -> Page:
    if state.water_level > 0:
        status = "The plant is fine. Water level: " + str(state.water_level)
    else:
        status = "The plant is THIRSTY."
    return Page(state, [
        Header("Plant Monitor"),
        status + "\n",
        Button("Water it", "water"),
        Button("Wait a day", "wait")
    ])


@route
def water(state: State) -> Page:
    state.water_level = 3
    return index(state)


@route
def wait(state: State) -> Page:
    if state.water_level > 0:
        state.water_level = state.water_level - 1
    return index(state)


start_server(State(2))
```

Compute what varies into a variable (`status`), then build one
content list. Keeping the `Page(...)` call single and flat is kinder
to future you than duplicating it in each branch.

## Recipe: a helper that returns components

When a branch decides more than a string, move it into a helper
function that returns a component (or a list of them), and drop the
call into the content:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    unread: int


def inbox_badge(unread: int) -> PageContent:
    if unread == 0:
        return "No new messages.\n"
    return bold(change_color(str(unread) + " new messages!\n", "crimson"))


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pigeon Post"),
        inbox_badge(state.unread),
        Button("A pigeon arrives", "arrive"),
        Button("Read everything", "read_all")
    ])


@route
def arrive(state: State) -> Page:
    state.unread = state.unread + 1
    return index(state)


@route
def read_all(state: State) -> Page:
    state.unread = 0
    return index(state)


start_server(State(0))
```

Routes return pages; helpers return everything smaller. The rule of
thumb: as soon as an `if` in a route wants to produce components, it
wants to be a helper.

## Recipe: one route for many items

Give every button the same target and an `Argument` naming its item.
The route receives the name and finds the item itself:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str


@dataclass
class State:
    pets: list[Pet]
    viewing: str


@route
def index(state: State) -> Page:
    content = [Header("The Registry")]
    for pet in state.pets:
        content.append(Button(pet.name, "show", [Argument("who", pet.name)]))
        content.append("\n")
    return Page(state, content)


@route
def show(state: State, who: str) -> Page:
    state.viewing = who
    found = "a mystery"
    for pet in state.pets:
        if pet.name == who:
            found = pet.species
    return Page(state, [
        Header(who),
        who + " is " + found + ".\n",
        Link("Back to the registry", "index")
    ])


start_server(State([
    Pet("Ada", "a corgi"),
    Pet("Babbage", "a small black mutt"),
    Pet("Captain", "a grey cat")
], ""))
```

Adding a pet to the list adds a button and a working detail page,
with no new code. This is the pattern the
[quiz game](../tutorials/quiz-game.md) is built on.

## Variations

- Branch on an argument instead of state:
  `Argument("mode", "simple")` on one button and
  `Argument("mode", "expert")` on another, one route reading `mode`.
- Show a section only sometimes by appending to the content list
  inside an `if`, instead of computing a string.
- Handle the empty case first: `if not state.pets:` return a page
  that says so, then write the normal page below it.

## Common problems

- **Both branches show at once, or neither**: the branch must choose
  what goes *into* the content list; check that you are not
  accidentally appending in both arms.
- **`missing parameter` on the shared route**: every button targeting
  it must carry the `Argument` it expects.
- **The route finds "a mystery"**: the argument's value did not match
  any item; compare exact spelling and case of the names.
- **You duplicated a page in two branches and they drifted**: compute
  the differences into variables or helpers, keep one `Page(...)`.

## Understand it

[Dynamic pages](../concepts/dynamic-pages.md): the concept behind
every recipe here.

## See another example

The [Shop](../examples/shop.md) drives an inventory with arguments;
the [Login flow](../examples/login.md) branches an entire page on
state.

## Look it up

[Argument](../reference/components/actions/argument.md),
[Button](../reference/components/actions/button.md), and
[route](../reference/route.md).

## Fix a problem

[Route is missing a parameter a form expected](../help/errors/missing-parameter.md)
and [Troubleshooting](../help/troubleshooting.md) for pages that
render the wrong branch.
