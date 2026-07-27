---
page_type: component
title: Button
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - Button
outcome: Trigger a route, optionally passing Arguments.
---

# Button

Group: [Actions](../index.md#actions)

## Description

A `Button` is a clickable control that runs a route. When clicked, it
gathers the values of any form fields on the page, sends them along,
and shows whatever page the target route returns. Use a `Button` for
doing things ("Feed", "Submit", "Play"); use a [Link](link.md) for
going places.

## Syntax

```python
Button(text, url)
Button(text, url, arguments)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `text` | `str` | required | The label shown on the button. |
| `url` | `str` | required | The name of the target route, as a string, such as `"feed"` for the route defined by `def feed(...)`. |
| `arguments` | see below | `None` | Extra values delivered to the target route's parameters. |

`arguments` accepts a single [Argument](argument.md), a list of
`Argument` objects, or a list of `(name, value)` pairs. Each one fills
the target route's parameter of the same name.

Like every component, `Button` also accepts
[styling and attribute keywords](../../keyword-attributes.md).

## Examples

The smallest button changes state and shows the result:

```python drafter height=200
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Ada the corgi has had " + str(state.treats) + " treats.\n",
        Button("Give a treat", "feed")
    ])


@route
def feed(state: State) -> Page:
    state.treats = state.treats + 1
    return index(state)


start_server(State(0))
```

A button submits the form fields on its page; the values arrive as
parameters named after each field:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    greeting: str


@route
def index(state: State) -> Page:
    return Page(state, [
        state.greeting + "\n",
        "Your name:",
        TextBox("visitor"),
        "\n",
        Button("Say hello", "greet")
    ])


@route
def greet(state: State, visitor: str) -> Page:
    state.greeting = "Hello, " + visitor + "!"
    return index(state)


start_server(State("Hello, whoever you are!"))
```

With `arguments`, several buttons can share one route and tell it
which was clicked:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    activity: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Captain the cat is currently: " + state.activity + "\n",
        Button("Nap time", "act", [Argument("choice", "napping")]),
        Button("Play time", "act", [Argument("choice", "playing")])
    ])


@route
def act(state: State, choice: str) -> Page:
    state.activity = choice
    return index(state)


start_server(State("sitting"))
```

## Notes

- A button whose `url` names no existing route stops the page with a
  [points to non-existent page](../../../help/errors/route-not-found.md)
  error. Check the spelling against the route function's name.
- Two buttons can point at the same route; use `arguments` to tell
  them apart, as above.
- While a click is being processed, the button can show a loading
  spinner; see `set_button_spinners` in
  [Site configuration](../../site-config.md).
- In tests, pages compare by structure:
  `assert_has(index(State(0)), Button("Give a treat", "feed"))`.

## Accessibility

Button text is what screen readers announce, so make it name the
action ("Give a treat"), not a vague "Click here". Buttons are
keyboard-operable by default; do not replace them with styled text.

## Related components

- [Link](link.md): the going-places counterpart.
- [Argument](argument.md): the values a button can carry.
- Inputs like [TextBox](../input/textbox.md) supply the form values a
  button submits.

## External links

- [The button element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/button)
