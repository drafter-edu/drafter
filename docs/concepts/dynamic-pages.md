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

That last technique deserves attention, because it changes how you
design apps. Without arguments, a quiz with ten questions would need
ten routes. With them, one `ask` route can serve any question,
because each question is *data* (an item in a list) rather than
*code* (a hand-written route). To add an eleventh question, you add
an item to the list instead of writing a new function.

Three tools make routes dynamic, and they can be combined:

- **Conditionals**: write `if state.score > 5:` to show one thing
  when the condition holds and something else otherwise.
- **Loops**: build the content list piece by piece with `append`,
  adding one piece per item of data.
- **[Argument](../reference/components/actions/argument.md)**: a
  button that carries a value, so several buttons can share one route
  and the route can still tell which button was clicked.

## See it

In the example below, three buttons share one route, and the page
you see next is chosen by an argument and the state together:

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

Trace the cause and effect: the loop makes one line per pet, the
`if` decides what that line says, and each Feed button carries its
pet's name, which tells the single `feed` route which pet to change.
As you feed the pets, watch the page rebuild to match the new state.

## What this means for your code

- Content lists do not have to be literal. Start with
  `content = [...]`, grow it with `append` inside loops and
  conditionals, and hand the finished list to `Page`.
- When several buttons differ only in *which thing* they act on, give
  them one route and an `Argument` naming the thing. Route-per-button
  is for buttons that do different *kinds* of things.
- To look up an item using a value from an argument, use a loop and
  an `if`, as `feed` does. The argument is plain data; nothing but
  your code connects it to the pet.
- Empty cases are part of the design. Decide what the page should
  show when the list has nothing in it, and show that on purpose.
- Dynamic routes are still ordinary functions, so tests can call them
  directly: the `assert_state` above checks feeding by name without
  clicking anything.

## Where people get confused

- **"I need a route for every page the visitor can see."** You need
  a route for every *kind* of page. One route can produce a thousand
  pages if the differences come from data.
- **"The argument is magic."** `Argument("pet_name", pet.name)`
  fills the parameter `pet_name`, exactly like a form field with that
  name would. The contract is the same; only the source of the value
  differs.
- **"The page updated wrong, so state must be broken."** Usually the
  state is right and the route's branches do not cover it. Check the
  debug panel's Current tab, then re-read the route asking "what does
  it build for *this* state?"
- **"I changed the list but the page did not change."** Pages are
  built when a route runs. Change the state, then rebuild the page by
  returning `index(state)` again.

## Go deeper

- [Show different content](../add/show-different-content.md) and
  [Show a collection of items](../add/show-a-collection.md) are the
  task pages that put this idea to work.
- [Make a quiz game](../tutorials/quiz-game.md) walks through a whole
  app built on this idea.
- [Live updates](live-updates.md) explains how to change *part* of a
  page instead of rebuilding all of it.
- [The Shop example](../examples/shop.md) uses arguments to manage an
  inventory.
