---
page_type: component
title: Argument
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Argument
outcome: Pass extra values to a route.
---

# Argument

Group: [Actions](../index.md#actions)

## Description

An `Argument` is an extra value that a button or link delivers to
its route, filling a parameter by name exactly the way a form field
would. Arguments let several buttons share one route while still
telling that route which button was clicked, which is the basis of
the [one-route-many-items pattern](../../../add/show-different-content.md).

## Syntax

```python
Button("Label", "target_route", [Argument(name, value)])
Argument(name, value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The target route's parameter to fill. Must be a valid Python parameter name. |
| `value` | JSON-safe | required | The value to deliver: strings, numbers, booleans, or lists of those. |

## Examples

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    last_wish: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "The genie last heard: " + state.last_wish + "\n",
        Button("Wish for gold", "wish", [Argument("wish_for", "gold")]),
        Button("Wish for time", "wish", [Argument("wish_for", "time")]),
        Button("Wish for naps", "wish", [Argument("wish_for", "naps")])
    ])


@route
def wish(state: State, wish_for: str) -> Page:
    state.last_wish = wish_for
    return index(state)


start_server(State("nothing yet"))
```

## Notes

- A button or link accepts a single `Argument`, a list of them, a
  list of `(name, value)` pairs, or a dictionary such as
  `{"wish_for": "gold"}`. Each entry fills the route parameter with
  the same name, so several entries fill several parameters.
  [Passing arguments](button.md#passing-arguments) on the Button
  page shows all four forms.
- An argument given to a `Button` or `Link` is stored on that one
  button or link, and only a click on that component delivers it.
  This is why the three buttons in the example can each carry a
  different `wish_for` value.
- An `Argument` placed directly in a page's content list behaves
  differently. Drafter renders it as a hidden input, so every button
  and link on the page delivers its value, the same way they deliver
  the contents of a `TextBox`. A hidden-input argument also follows
  the rule for inputs that its name must be unique on the page, and
  a second component with the same name causes a
  [duplicate-name error](../../../help/errors/duplicate-component-name.md).
- When a button's argument and an input on the page have the same
  name, the route receives the argument's value, and the debug panel
  warns that the name was provided more than once.
- The `arguments` keyword also works on any component that has an
  `on_*` event handler.
  `TextBox("amount", on_change="update", arguments={"row": 3})`
  calls `update` with `row` set to `3` each time the box changes.
- Values must be JSON-safe (text, numbers, booleans, or lists of
  those). Passing a whole dataclass is not supported; instead, pass
  a name or index and look the object up inside the route, as the
  [shop example](../../../examples/shop.md) does.
- An argument whose name matches no parameter of the target route
  does not stop the page. The route runs without that value. The
  opposite mistake is an error, because a route parameter that no
  argument or input fills produces a
  [missing-parameter](../../../help/errors/missing-parameter.md)
  error page. A misspelled argument name therefore usually causes
  both problems at once. For the unmatched name, the debug panel
  shows a warning like this one:

    ```text
    The component argument 'wish_fr' was sent to 'wish', but the function has no matching parameter.
    ```

## Related components

- [Button](button.md) and [Link](link.md): the components that
  carry arguments to a route.
- [Show different content](../../../add/show-different-content.md):
  the how-to guide built around this component.

## External links

- [Hidden inputs on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/hidden)
