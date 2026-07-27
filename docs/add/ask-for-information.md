---
page_type: how-to
title: Ask the user for information
level: L2
audience: S
priority: P0
prereqs: [start/first-app]
symbols: []
outcome: Build working forms.
---

# Ask the user for information

## Goal

You want the visitor to type, pick, or check something, and you want
those values delivered to your code.

## Before you start

You can build pages with buttons. One rule appears everywhere on this
page: an input's **name** becomes the **parameter** with the same name
in the route the button goes to.

## The smallest version

This form asks one question and delivers one answer:

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "What should we call you?",
        TextBox("name"),
        "\n",
        Button("Save", "save_name")
    ])


@route
def save_name(state: State, name: str) -> Page:
    state.name = name
    return Page(state, [
        "Nice to meet you, " + state.name + "!\n",
        Button("Change it", "index")
    ])


start_server(State(""))
```

Put a plain string right before each input as its label, and save the
parameter into state if you need it after this click.

## Recipe: one form, several kinds of input

`TextBox` collects a line of text, `SelectBox` offers a fixed list of
choices, and `CheckBox` collects a yes/no. One button delivers all three
to one route, and the tests at the bottom check it without any clicking:

```python drafter height=400
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    replies: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Party invitation form.\n",
        "Your name:",
        TextBox("name"),
        "\nPick a meal:",
        SelectBox("meal", ["pizza", "salad", "soup"]),
        "\nBringing a guest?",
        CheckBox("guest"),
        "\n",
        Button("RSVP", "rsvp")
    ])


@route
def rsvp(state: State, name: str, meal: str, guest: bool) -> Page:
    state.replies = state.replies + 1
    lines = [
        name + " wants " + meal + ".\n"
    ]
    if guest:
        lines.append("They are bringing a guest.\n")
    lines.append("Replies so far: " + str(state.replies) + "\n")
    lines.append(Button("Next reply", "index"))
    return Page(state, lines)


assert_has(rsvp(State(0), "Ada", "pizza", False), "Ada wants pizza")
assert_has(rsvp(State(0), "Babbage", "soup", True), "bringing a guest")
assert_state(rsvp(State(4), "Domino", "salad", False), State(5))

start_server(State(0))
```

The `CheckBox` arrives as a `bool` because the parameter is annotated
`guest: bool`; checked is `True`, unchecked is `False`.

## Recipe: numbers instead of text

Annotate the parameter as `int` (or `float`) and give the box a sensible
starting value, so the form cannot arrive empty:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Tickets cost 5 gold each.\n",
        "How many tickets?",
        TextBox("tickets", 2),
        "\n",
        Button("Get the price", "price")
    ])


@route
def price(state: State, tickets: int) -> Page:
    state.total = tickets * 5
    return Page(state, [
        str(tickets) + " tickets cost " + str(state.total) + " gold.\n",
        Button("Change the order", "index")
    ])


assert_state(price(State(0), 3), State(15))

start_server(State(0))
```

If the visitor types something that is not a whole number, Drafter shows
a friendly error naming the parameter and the value, and they can go back
and fix it.

## Recipe: longer text

`TextArea` works like `TextBox` but gives the visitor room to type
several lines. The name-to-parameter contract is the same:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    review: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Review our arcade:",
        "\n",
        TextArea("review", state.review),
        "\n",
        Button("Submit review", "thank_you")
    ])


@route
def thank_you(state: State, review: str) -> Page:
    state.review = review
    return Page(state, [
        "Thanks! You wrote:\n",
        state.review + "\n",
        Button("Edit your review", "index")
    ])


start_server(State(""))
```

Handing `state.review` back to the `TextArea` as its starting value gives
the visitor an edit loop instead of a blank box.

## Common problems

- **A missing-parameter error**: an input name and a parameter name do
  not match exactly. The error names the expected parameter; compare
  spelling and underscores.
- **A number arrives as text**: the parameter has no annotation. Write
  `tickets: int`.
- **The value vanishes after the next click**: a parameter's value only
  lasts for that one route call. Save it into a `state` field, as every
  recipe above does.
- **Two buttons, one form**: both target routes receive the same inputs,
  so both need the matching parameters.

## Understand it

[Forms and input](../concepts/forms-and-input.md) explains the
name-to-parameter contract and includes the type conversion table.

## See another example

[Big form](../examples/forms.md) shows every core input in one place,
and the [story maker](../tutorials/story-maker.md) shows forms driving a
whole app.

## Look it up

[TextBox](../reference/components/input/textbox.md),
[TextArea](../reference/components/input/textarea.md),
[CheckBox](../reference/components/input/checkbox.md), and
[SelectBox](../reference/components/input/selectbox.md).

## Fix a problem

[Route is missing a parameter](../help/errors/missing-parameter.md) and
[Could not convert text to an int](../help/errors/type-conversion-int.md).
