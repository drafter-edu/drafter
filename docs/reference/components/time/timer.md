---
page_type: component
title: Timer
level: L4
audience: S
priority: P1
prereqs: []
symbols:
  - Timer
outcome: Run a countdown that fires a route.
---

# Timer

Group: [Time](../index.md#time)

## Description

A `Timer` counts down from a duration and calls a route when it
reaches zero. It can also call a route on every tick along the way.
This is how quizzes get time limits, games get countdowns, and
messages disappear after a few seconds.

## Syntax

```python
Timer(duration, "route_name")
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `duration` | `int` | required | How long the countdown lasts, in milliseconds (5 seconds is `5000`). |
| `on_finish` | `str` | required | The name of the route to call when the countdown reaches zero. |
| `show` | `bool` | `True` | Display the remaining time on the page. |
| `controls` | `bool` | `False` | Show pause and restart buttons next to the timer. |
| `persistent` | `bool` | `False` | Keep the countdown running when the page re-renders. Without this, every re-render starts a fresh timer. |
| `rate` | `int` | `1000` | Milliseconds between ticks. |
| `on_tick` | `str` | none | The name of a route to call on every tick. |

## Examples

A five-second clicking contest. The timer is `persistent`, because
every click re-renders the page and a non-persistent timer would
start over each time:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clicks: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Speed Clicker"),
        "Pet Babbage as many times as you can in 5 seconds!\n",
        "Pets so far: " + str(state.clicks) + "\n",
        Timer(5000, "times_up", persistent=True),
        "\n",
        Button("Pet the dog", "pet")
    ])


@route
def pet(state: State) -> Page:
    state.clicks = state.clicks + 1
    return index(state)


@route
def times_up(state: State) -> Page:
    return Page(state, [
        Header("Time's up!"),
        "Babbage got " + str(state.clicks) + " pets. Good dog."
    ])


start_server(State(0))
```

A tick route receives the remaining time, so you can display the
countdown your own way. Here `show=False` hides the built-in
display and the page text does the announcing:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    seconds_left: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Rocket Launch"),
        "Launching in " + str(state.seconds_left) + "...\n",
        Timer(10000, "launch", on_tick="tick",
              show=False, persistent=True)
    ])


@route
def tick(state: State, remaining: int) -> Page:
    state.seconds_left = remaining // 1000
    return index(state)


@route
def launch(state: State) -> Page:
    return Page(state, [Header("Liftoff!")])


start_server(State(10))
```

## Notes

- All times are in milliseconds: `1000` is one second.
- `on_finish` and `on_tick` take route names as strings, the same
  way a [Button](../actions/button.md) does.
- The finish and tick routes can receive two extra parameters by
  name: `remaining` (milliseconds left) and `duration` (the total),
  both whole numbers.
- Set `persistent=True` whenever other routes re-render the page
  while the countdown should keep going. A non-persistent timer is
  rebuilt, and therefore restarted, on every render.
- A tick route that re-renders the whole page (like `tick` above)
  runs once per tick; keep `rate` at one second or slower for that
  pattern.

## Related components

- [Clock](clock.md): counts up forever instead of down.
- [RemovePersistent](removepersistent.md): stop a persistent timer
  from a later page.

## External links

- [Live updates](../../../concepts/live-updates.md): how events
  calling routes works in general.
