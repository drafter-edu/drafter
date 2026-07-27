---
page_type: how-to
title: Make things happen over time
level: L4
audience: S
priority: P2
prereqs: [add/live-behavior]
symbols: []
outcome: Add countdowns, ticks, and clocks.
---

# Make things happen over time

## Goal

You want your app to act on a schedule instead of waiting for a
click: a quiz question that expires, a game that earns points
every second, or a countdown the visitor can watch.

## Before you start

You can [add live behavior](live-behavior.md): timed features use
the same machinery, with time as the event instead of typing. Two
components drive everything here.
[Timer](../reference/components/time/timer.md) counts down from a
duration and calls a route when it reaches zero.
[Clock](../reference/components/time/clock.md) never stops; it
calls a route on every tick. Both measure in milliseconds, so one
second is `1000`.

## Recipe: a question that expires

The timer's `on_finish` route takes over when time runs out. The
visitor either answers first or meets the "too slow" page:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    answered: bool


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Quick! 10 seconds!"),
        "Which pet is the grey cat?\n",
        Timer(10000, "too_slow"),
        "\n",
        Button("Ada", "wrong"),
        Button("Captain", "right"),
        Button("Domino", "wrong")
    ])


@route
def right(state: State) -> Page:
    state.answered = True
    return Page(state, ["Correct, with time to spare."])


@route
def wrong(state: State) -> Page:
    state.answered = True
    return Page(state, ["Wrong, but at least you were fast."])


@route
def too_slow(state: State) -> Page:
    return Page(state, ["Time ran out before you chose!"])


start_server(State(False))
```

Answering navigates away, which tears the timer down; nothing
extra is needed to cancel it.

## Recipe: a game that ticks

A `Clock` calls its route on every tick. Answering with a
`Fragment` keeps the rest of the page untouched, so the clock
itself never restarts:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Idle Corgi"),
        "Ada finds a treat every second, and two when you help.\n",
        Clock(1000, "tick", show=False),
        Output("score", ["Treats: " + str(state.treats)]),
        "\n",
        Button("Help her look", "help_look")
    ])


@route
def tick(state: State) -> Fragment:
    state.treats = state.treats + 1
    return Fragment(["Treats: " + str(state.treats)],
                    target="#score")


@route
def help_look(state: State) -> Page:
    state.treats = state.treats + 2
    return index(state)


start_server(State(0))
```

## Giving the visitor control

Both components accept `controls=True`, which adds pause and
restart buttons next to the display, and `show=False`, which
hides the built-in display when your page presents the time its
own way (as the tick route above does).

## Keeping time across page changes

A timer or clock is part of the page that created it, so
navigating away normally ends it, and re-rendering the page
normally restarts it. Pass `persistent=True` when the countdown
should survive both, like a game clock that keeps running while
the visitor checks an inventory page. A persistent component
keeps going until you remove it with
[RemovePersistent](../reference/components/time/removepersistent.md).

## Common problems

- **The countdown restarts every time I click something**: the
  route re-rendered the page, rebuilding the timer. Either answer
  with a `Fragment` (as the tick recipe does) or mark the timer
  `persistent=True`.
- **The clock keeps running after the visitor leaves the page**:
  that is what `persistent=True` asks for; remove the keyword, or
  end it with `RemovePersistent`.
- **The timer finished but nothing happened**: `on_finish` must
  name a real route as a string; check the spelling against the
  route's function name.
- **Two clocks are ticking at once**: each render of a
  non-persistent clock creates a fresh one, but a persistent
  clock plus a re-rendered copy can overlap. Give one component
  the responsibility.

## Understand it

[Live updates](../concepts/live-updates.md) explains events and
fragments, which is all a tick really is.

## See another example

The [Timer reference page](../reference/components/time/timer.md)
builds a clicking contest and a rocket countdown with the same
pieces.

## Look it up

[Timer](../reference/components/time/timer.md),
[Clock](../reference/components/time/clock.md), and
[RemovePersistent](../reference/components/time/removepersistent.md).
For letting the visitor enter a time of day, see
[DateInput and friends](../reference/components/input/dateinput.md).

## Fix a problem

[Troubleshooting](../help/troubleshooting.md) covers routes that
never fire; the checks there apply to `on_finish` and `on_tick`
targets too.
