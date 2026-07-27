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

An `Argument` is a value a button or link carries to its route,
filling a parameter by name, exactly the way a form field would.
It is how several buttons share one route and still tell it apart
which was clicked, the backbone of the
[one-route-many-items pattern](../../../add/show-different-content.md).

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

- A button accepts a single `Argument`, a list of them, or a list
  of `(name, value)` pairs; several arguments fill several
  parameters.
- Arguments render as hidden inputs, so their values ride along
  with the form like any other field, and share the same rules:
  a name colliding with a real input's name is a
  [duplicate-name error](../../../help/errors/duplicate-component-name.md),
  and a name matching no parameter is
  [missing-parameter](../../../help/errors/missing-parameter.md)
  territory in reverse.
- Values must be JSON-safe (text, numbers, booleans, lists);
  passing whole dataclasses is not supported: pass a name or index
  and look the object up in the route, as the
  [shop example](../../../examples/shop.md) does.

## Related components

- [Button](button.md) and [Link](link.md): the carriers.
- [Show different content](../../../add/show-different-content.md):
  the how-to built on this component.

## External links

- [Hidden inputs on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/hidden)
