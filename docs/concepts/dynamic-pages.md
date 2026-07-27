---
page_type: concept
title: Dynamic pages
level: L3
audience: S
priority: P1
prereqs: [concepts/forms-and-input]
symbols: []
outcome: Make one route render differently based on state and arguments.
---

# Dynamic pages

## In one sentence

A dynamic page is what you get when one route builds different pages
from the same code, depending on state and arguments.

## The idea

A route is not a page; it is a function that builds one. Nothing says
it must build the same one every time. A route can look at the state
and branch, loop over a list to decide how much content to make, or
receive an argument telling it which of many similar pages to build
this time.

That last trick deserves attention, because it changes how you design
apps. Without it, a quiz with ten questions wants ten routes. With
it, one `ask` route serves any question, because the question is
*data* (an item in a list) rather than *code* (a hand-written route).
Adding an eleventh question means adding a list item, not writing a
function.

Three tools make routes dynamic, and they compose:

- **Conditionals**: `if state.score > 5:` show one thing, otherwise
  another.
- **Loops**: build the content list piece by piece with `append`, one
  piece per item of data.
- **[Argument](../reference/components/actions/argument.md)**: a
  button that carries a value, so several buttons can share one route
  and tell it apart which was clicked.

## See it

One route, three buttons, three different pages, chosen by an
argument and the state together:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    fed: bool


@dataclass
class State:
    pets: list[Pet]


@route
def index(state: State) -> Page:
    content = [Header("The Pet Hotel")]
    for pet in state.pets:
        if pet.fed:
            content.append(pet.name + " is fed and happy.\n")
        else:
            content.append(pet.name + " is hungry! ")
            content.append(Button("Feed " + pet.name, "feed",
                                  [Argument("pet_name", pet.name)]))
            content.append("\n")
    return Page(state, content)


@route
def feed(state: State, pet_name: str) -> Page:
    for pet in state.pets:
        if pet.name == pet_name:
            pet.fed = True
    return index(state)


assert_state(
    feed(State([Pet("Ada", "corgi", False)]), "Ada"),
    State([Pet("Ada", "corgi", True)]))

start_server(State([
    Pet("Ada", "corgi", False),
    Pet("Captain", "cat", False),
    Pet("Domino", "cat", True)
]))
```

Cause and effect: the loop makes one line per pet, the `if` decides
what that line says, and each Feed button carries its pet's name so
the single `feed` route knows which pet to change. Watch the page
reshape itself as you feed them.

## What this means for your code

- Content lists do not have to be literal. Start with
  `content = [...]`, grow it with `append` inside loops and
  conditionals, and hand the finished list to `Page`.
- When several buttons differ only in *which thing* they act on, give
  them one route and an `Argument` naming the thing. Route-per-button
  is for buttons that do different *kinds* of things.
- Look things up by a value from an argument with a loop and an `if`,
  as `feed` does. The argument is plain data; nothing but your code
  connects it to the pet.
- Empty cases are part of the design: what does the page show when
  the list has nothing in it? Decide, and show something on purpose.
- Dynamic routes are still just functions, so tests drive them
  directly: the `assert_state` above checks feeding by name without
  clicking anything.

## Where people get confused

- **"I need a route for every page the visitor can see."** You need
  a route for every *kind* of page. One route can produce a thousand
  pages if the differences come from data.
- **"The argument is magic."** `Argument("pet_name", pet.name)` just
  fills the parameter `pet_name`, exactly like a form field with that
  name would. Same contract, different source.
- **"The page updated wrong, so state must be broken."** Usually the
  state is right and the route's branches do not cover it. Check the
  debug panel's Current tab, then re-read the route asking "what does
  it build for *this* state?"
- **"I changed the list but the page did not change."** Pages are
  built when a route runs. Mutate the state, then re-render by
  returning `index(state)` again.

## Go deeper

- [Show different content](../add/show-different-content.md) and
  [Show a collection of items](../add/show-a-collection.md): the
  task pages.
- [Make a quiz game](../tutorials/quiz-game.md): a whole app built on
  this idea.
- [Live updates](live-updates.md): changing *part* of a page instead
  of rebuilding it all.
- [The Shop example](../examples/shop.md): arguments driving an
  inventory.
