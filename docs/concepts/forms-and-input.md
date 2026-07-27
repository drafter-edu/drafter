---
page_type: concept
title: Forms and input
level: L2
audience: S
priority: P0
prereqs: [concepts/routes-and-pages, concepts/state]
symbols: []
outcome: Explain how a form field's value reaches a route function.
---

# Forms and input

## In one sentence

A form field's **name** becomes a **parameter** of the route the button
goes to: that name-to-parameter match is the whole contract, and the
parameter's type annotation tells Drafter what to convert the text into.

## The idea

Input components like `TextBox` and `CheckBox` collect values from the
visitor. Each one is created with a name:

```python
TextBox("new_name")
```

When the visitor clicks a `Button`, Drafter gathers every input on the
page and delivers each one to the button's target route **as the
parameter with the same name**. A page with `#!python TextBox("new_name")`
means the target route must have a parameter called `new_name`:

```python
@route
def greet(state: State, new_name: str) -> Page:
    ...
```

The names must match exactly. The value arrives as text unless the
parameter's annotation says otherwise:

| Annotation | The visitor typed | The route receives |
| ---------- | ----------------- | ------------------ |
| `str`      | `Ada`             | `#!python "Ada"`   |
| `int`      | `42`              | `#!python 42`      |
| `float`    | `3.5`             | `#!python 3.5`     |
| `bool`     | (a checked box)   | `#!python True`    |

If the text cannot be converted, for example `abc` for an `int`
parameter, Drafter stops with a friendly error naming the parameter and
the value, and the visitor can go back and correct it.

## See it

The contract in its smallest form. Follow the name `new_name` from the
`TextBox`, to the button's target route, to the parameter:

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "What is your name?",
        TextBox("new_name"),
        "\n",
        Button("Greet me", "greet")
    ])


@route
def greet(state: State, new_name: str) -> Page:
    state.name = new_name
    return Page(state, [
        "Hello, " + state.name + "!\n",
        Button("Start over", "index")
    ])


assert_state(greet(State(""), "Ada"), State("Ada"))

start_server(State(""))
```

The test at the bottom shows something useful: because routes are
functions, you can hand them input values directly. No typing, no
clicking, and the contract still holds.

Several inputs on one page become several parameters, and annotations do
the converting. Type numbers into this one, then try typing `abc` into a
box to see the conversion error:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "The last total was " + str(state.total) + ".\n",
        "Pick two whole numbers to add:",
        TextBox("first", 3),
        TextBox("second", 4),
        "\n",
        Button("Add them", "add")
    ])


@route
def add(state: State, first: int, second: int) -> Page:
    state.total = first + second
    return index(state)


assert_state(add(State(0), 3, 4), State(7))

start_server(State(0))
```

The `#!python TextBox("first", 3)` form gives the box a starting value of
`3`. Defaults keep a form from ever submitting an empty string where a
number is expected.

## What this means for your code

- Choose input names as carefully as variable names; they *become*
  parameter names. `new_name` and `first` read well; `textbox1` does not.
- The button's target route must accept one parameter per input on the
  page, matching each name exactly.
- Annotate every input parameter. `#!python age: int` gets you a number
  or a clear error; an unannotated parameter gets you text you must
  convert yourself.
- Store what matters into `state` inside the route. Parameters live only
  for that one call; state is what persists to the next page.
- Test form routes by calling them directly with sample values, as both
  examples above do.

## Where people get confused

- **"My route says a parameter is missing"**: the input's name and the
  parameter's name differ, often by one letter or an underscore. Compare
  them character by character; the error message names the parameter it
  expected.
- **"The value is a string even though it is a number"**: the parameter
  has no type annotation. Text is the default; annotations opt into
  conversion.
- **"Where did my typed value go after the next click?"** Parameters are
  delivered once, to one route. If the value should live longer, assign
  it to a `state` field.
- **"Can one page have two buttons to different routes?"** Yes, and both
  routes receive the same page's inputs, so both need the matching
  parameters.

## Go deeper

- [Ask the user for information](../add/ask-for-information.md): recipes
  for every input component.
- [State](state.md): where values go when they need to outlive the click.
- [Type conversion errors](../help/errors/type-conversion-int.md): the
  error entry for failed conversions.
- [Dynamic pages](dynamic-pages.md): routes whose output depends on
  their inputs.
