---
page_type: component
title: Clock
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Clock
outcome: Run a repeating tick route.
---

# Clock

Group: [Time](../index.md#time)

## Description

A `Clock` counts up forever, calling a route on every tick. It
is the heartbeat for anything ongoing: an idle game earning
points, an elapsed-time display, a slideshow that advances by
itself. When the counting should end and something should
happen, that is a [Timer](timer.md); a clock never finishes.

## Syntax

```python
Clock(interval, "route_name")
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `interval` | `int` | required | Milliseconds between ticks (one second is `1000`). |
| `route` | `str` | required | The name of the route to call on each tick. |
| `show` | `bool` | `True` | Display the elapsed time on the page. |
| `controls` | `bool` | `False` | Show pause and restart buttons. |
| `persistent` | `bool` | `False` | Keep counting through page re-renders and page changes. |
| `on_tick` | `str` | none | Alternative keyword spelling of `route`. |

## Examples

A slideshow that advances every three seconds. The tick route
returns a `Fragment`, so the clock itself is never rebuilt:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    position: int


CAPTIONS = [
    "Ada guards the front window.",
    "Babbage has located a sunbeam.",
    "Captain judges everyone from the shelf.",
    "Domino is somewhere. Probably."
]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet Cam Highlights"),
        Clock(3000, "advance", show=False),
        Output("caption", [CAPTIONS[state.position]])
    ])


@route
def advance(state: State) -> Fragment:
    state.position = (state.position + 1) % len(CAPTIONS)
    return Fragment([CAPTIONS[state.position]], target="#caption")


start_server(State(0))
```

## Notes

- The tick route can receive two parameters by name: `elapsed`
  (milliseconds since the clock started) and `interval` (the
  current tick spacing).
- A tick route that returns a whole `Page` rebuilds the clock,
  restarting its elapsed count; return a `Fragment` or an
  `Update`, or mark the clock `persistent=True`.
- A route slower than the interval delays later ticks; they do
  not pile up.
- A persistent clock outlives page changes; end it from a later
  page with [RemovePersistent](removepersistent.md).

## Related components

- [Timer](timer.md): counts down and finishes.
- [RemovePersistent](removepersistent.md): stopping a persistent
  clock.

## External links

- [Make things happen over time](../../../add/timers.md): the
  recipes.
