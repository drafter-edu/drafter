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

## Recipe: check the answer and ask again

Visitors type things your code cannot use: words where a number
belongs, or a number that is too large. Checking an answer before
using it is called validating it. When the answer fails the check,
show the form again with a message that says what to fix, and keep
what the visitor typed so they can correct it.

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    tickets: str
    problem: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Ticket booth"),
        state.problem,
        "How many tickets would you like (1 to 10)?",
        TextBox("tickets", state.tickets),
        "\n",
        Button("Buy", "buy")
    ])


@route
def buy(state: State, tickets: str) -> Page:
    state.tickets = tickets
    if not tickets.isdigit():
        state.problem = "Please type a whole number.\n"
        return index(state)
    if int(tickets) < 1 or int(tickets) > 10:
        state.problem = "You can buy between 1 and 10 tickets.\n"
        return index(state)
    state.problem = ""
    cost = int(tickets) * 5
    return Page(state, [
        "You bought " + tickets + " tickets for " + str(cost) + " gold.\n",
        Button("Buy more", "index")
    ])


assert_has(buy(State("", ""), "lots"), "Please type a whole number.")
assert_has(buy(State("", ""), "40"), "between 1 and 10")
assert_has(buy(State("", ""), "3"), "You bought 3 tickets for 15 gold.")

start_server(State("2", ""))
```

Three decisions make this work:

- The `tickets` parameter is annotated `str`, not `int`. Drafter then
  hands over exactly what was typed, and the route decides whether it
  is a number. With an `int` annotation, Drafter would stop at its own
  error page before the route ever ran.
- The state has a `problem` field. The form page always displays it,
  and it is an empty string when there is nothing to report.
- When a check fails, the route sets the message and returns
  `index(state)`, so the visitor sees the same form again with their
  answer still in the box.

Each check gets its own test. Tests for input checks are worth
writing, because the mistakes are the cases you are least likely to
try by hand.

## More kinds of input

The recipes above use four input components. Drafter has more, and
every one follows the same rule: the component's name becomes a
parameter, and the parameter's annotation says what kind of value
arrives.

| The visitor... | Component | Annotate the parameter as |
| -------------- | --------- | ------------------------- |
| picks one option from a short visible list | [RadioButtonGroup](../reference/components/input/radiobuttongroup.md) | `str` |
| checks any number of boxes in a group | [RelatedCheckBox](../reference/components/input/relatedcheckbox.md) | `list[str]` |
| picks several options from one list | [SelectBox](../reference/components/input/selectbox.md) with `multiple=True` | `list[str]` |
| drags a slider to a number | [Slider](../reference/components/input/slider.md) | `int` or `float` |
| picks a color | [ColorPicker](../reference/components/input/colorpicker.md) | `str` |
| picks a date | [DateInput](../reference/components/input/dateinput.md) | `date` |
| picks a time of day | [TimeInput](../reference/components/input/timeinput.md) | `time` |
| picks a date and a time together | [DateTimeInput](../reference/components/input/datetimeinput.md) | `datetime` |
| chooses a file | [FileUpload](../reference/components/input/fileupload.md) | see [Upload and download files](files.md) |

The two `list[str]` rows deliver an empty list when nothing is
checked or selected. The `date`, `time`, and `datetime` types come
from Python's `datetime` module, so a route that uses them needs
`from datetime import date, time, datetime` at the top of the file.

## Common problems

- **A missing-parameter error**: an input name and a parameter name do
  not match exactly. The error names the expected parameter; compare
  spelling and underscores.
- **A number arrives as text**: the parameter has no annotation. Write
  `tickets: int`.
- **The value vanishes after the next click**: a parameter's value only
  lasts for that one route call. Save it into a `state` field, as every
  recipe above does.
- **Two buttons, one form**: every button on the page sends all of the
  page's inputs to its route. A route that needs a value must have the
  matching parameter. A route that does not need it, such as the target
  of a Cancel button, can leave the parameter out. The page still
  works, and the debug panel lists a warning about a form field with no
  matching parameter.

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
