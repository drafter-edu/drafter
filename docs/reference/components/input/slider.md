---
page_type: component
title: Slider
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Slider
outcome: Collect a number from a range.
---

# Slider

Group: [Input](../index.md#input)

## Description

A `Slider` shows a track with a handle the visitor drags. Each
position on the track stands for a number between a lowest and a
highest value, and the chosen number arrives at the route as a
parameter with the field's name. Use it when any number in a range
is acceptable and the exact figure matters less than "more" or
"less": a volume, a difficulty, a number of treats. When the visitor
needs to enter one precise number, a [TextBox](textbox.md) is the
better choice.

## Syntax

```python
Slider(name, min, max)
Slider(name, min, max, default_value)
Slider(name, min, max, default_value, step)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `min` | `int` or `float` | required | The lowest value, at the left end of the track. |
| `max` | `int` or `float` | required | The highest value, at the right end of the track. It must be larger than `min`. |
| `default_value` | `int` or `float` | the middle | Where the handle starts. It must lie from `min` to `max`. |
| `step` | `int` or `float` | `1` | How far apart the allowed values are. With `step=5` the handle stops on 0, 5, 10, and so on. |

## Examples

The route's parameter is annotated as `int`, so Drafter converts the
submitted text into a number:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Treat Planner"),
        "Ada the corgi gets " + str(state.treats) + " treats today.\n",
        "Fewer",
        Slider("treats", 0, 10, state.treats),
        "More\n",
        Button("Save", "save")
    ])


@route
def save(state: State, treats: int) -> Page:
    state.treats = treats
    return index(state)


start_server(State(3))
```

A fractional `step` lets the handle stop between whole numbers.
Annotate the parameter as `float` to match:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hours: float


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Nap Log"),
        "Captain napped for " + str(state.hours) + " hours.\n",
        Slider("hours", 0, 12, state.hours, step=0.5),
        "\n",
        Button("Record", "record")
    ])


@route
def record(state: State, hours: float) -> Page:
    state.hours = hours
    return index(state)


start_server(State(2.5))
```

## Notes

- A slider does not show its number. Say what the ends mean with
  text on either side (the "Fewer" and "More" above), and show the
  saved value somewhere on the page after the form is submitted.
- Annotate the receiving parameter as `int` when `step` is a whole
  number and as `float` when it is a fraction. An `int` annotation
  with a value like `2.5` is a
  [conversion error](../../../help/errors/type-conversion-int.md).
- A slider always submits a number; there is no "empty" position.
- Drafter checks the arguments when the slider is created. A `min`
  that is not below `max`, a `default_value` outside the range, or a
  `step` of zero raises an error that says which argument to fix.
- The browser decides what the track looks like, so it differs
  between computers and phones.

## Accessibility

A slider with no caption is a bare line on the page. Put a short
description right before it, or attach a [Label](label.md) with the
slider's name as its `for_id`, so people know what the number
controls. Sliders can be moved with the arrow keys as well as the
mouse.

## Related components

- [TextBox](textbox.md): collect one exact number.
- [SelectBox](selectbox.md): choose from a short list of named
  options instead of a range.
- [Meter](../data/meter.md): show a number within a range without
  letting the visitor change it.

## External links

- [The range input on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/range)
