---
page_type: component
title: Meter
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - Meter
outcome: Show a gauge value.
---

# Meter

Group: [Data display](../index.md#data-display)

## Description

A `Meter` is a gauge: it shows a measured value within a known
range, like a fuel gauge or a battery indicator. Given the
optional threshold arguments, the browser colors the bar to show
whether the value is in a good or bad zone, with no styling code
from you. Use [ProgressBar](progressbar.md) when the value means
"how close to done"; use `Meter` when it means "how much, on a
scale".

## Syntax

```python
Meter(value, min=0, max=100)
Meter(value, min=0, max=100, low=30, high=80, optimum=90)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `value` | number | required | The measurement to display. |
| `min` | number | `0` | The bottom of the scale. |
| `max` | number | `1` | The top of the scale. |
| `low` | number | none | Values below this count as the "low" zone. |
| `high` | number | none | Values above this count as the "high" zone. |
| `optimum` | number | none | Where the ideal value sits, which tells the browser whether low or high deserves the warning color. |

## Examples

Hunger gauges that change color as they leave the healthy zone,
because `optimum` marks low hunger as good:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Kennel Dashboard"),
        "Ada's hunger:\n",
        Meter(state.hunger, min=0, max=100,
              low=30, high=70, optimum=10),
        "\n",
        Button("Feed her", "feed"),
        Button("Wait an hour", "wait")
    ])


@route
def feed(state: State) -> Page:
    state.hunger = 0
    return index(state)


@route
def wait(state: State) -> Page:
    state.hunger = min(100, state.hunger + 30)
    return index(state)


start_server(State(50))
```

## Notes

- Without `min`/`max`, the scale runs 0 to 1; setting them is
  almost always clearer.
- The zone colors come from the browser and vary between
  browsers; treat them as a bonus, and state the number in text
  when the value matters.
- `optimum` is what flips the meaning: with `optimum` near
  `min`, high values show as bad; with `optimum` near `max`,
  low values do.

## Related components

- [ProgressBar](progressbar.md): completion rather than
  measurement.

## External links

- [The meter element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meter)
