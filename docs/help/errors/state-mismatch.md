---
page_type: error
title: State doesn't match the State class
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix state that no longer matches the State class.
error_text: "type changed from"
error_id: state.type_change
---

# State doesn't match the State class

## The error

```text
SiteState type changed from State to NoneType.
```

The friendly version: "One of your routes changed the site state from
State to NoneType; the state should keep the same type for the whole
site." This arrives as a warning, and the real trouble usually
follows one click later, as an `AttributeError` like
`'NoneType' object has no attribute 'score'` when the next route
tries to use the broken state.

## What it means

Every route receives the state and passes it onward through the
`Page` it returns. One of your routes handed back something of a
different type than your `State` class, most often `None`, and from
then on every route is working with the wrong thing.

## Where to look

The route that ran right before the warning appeared; the debug
panel's history shows which one that was. Look at the `Page(...)` it
returned.

## Check

- **A `Page` without state**: in a stateful app, `Page(["..."])`
  quietly means state `None`. Every route in a stateful app must
  return `Page(state, [...])` with the state first.
- **Returning the wrong value**: `Page(state.score, [...])` carries a
  number onward instead of the whole state.
- **Rebuilding instead of mutating**: a route that does
  `state = ["oops"]` or otherwise reassigns to something that is not
  your `State`.

## Fix

Give the returned `Page` the state, mutated but the same object and
type:

```python
@route
def gain(state: State) -> Page:
    state.score = state.score + 1
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        Button("Again", "gain")
    ])
```

## Confirm

The warning stops appearing, and the debug panel's Current tab shows
your `State` with its fields after every click. An
`assert_state(gain(State(0)), State(1))` test locks the shape in.

## Prevent

One habit covers it: every route takes `state` first and returns
`Page(state, [...])` first. When a route has nothing to remember, it
still passes the state through untouched.

A related situation: after you edit the `State` class itself (adding
or removing a field), old saved or replayed state no longer fits the
new class. Restart the app so it rebuilds state from
`start_server(State(...))`, and update any tests that construct the
old shape.

## Understand

[State](../../concepts/state.md) explains how state flows from route
to page to the next route, and why the type must stay stable.
