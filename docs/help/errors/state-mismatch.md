---
page_type: error
title: State doesn't match the State class
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix state that no longer matches the State class.
error_text: "State Changed Type"
error_id: payload.state_verification_failed
---

# State doesn't match the State class

## The error

The error page has this title:

```text
State Changed Type
```

The sentence under the title names the route and the two types
involved:

```text
The page returned from `gain` has a state that is a NoneType, but the
previous state was a State. The state must stay the same type from page
to page.
```

The technical message below it shows the value the route supplied
and the value the app had before:

```text
payload.state_verification_failed: State verification failed for the page 'gain':
The server did not return a valid Page() object from gain. The state object's
type changed from its previous type. The new value is:
 None
The most recent value was:
 State(score=0)
The expected type was:
 <class '__main__.State'>
Make sure you return the same type each time.
```

The error page appears as soon as the route returns. Drafter does
not accept the new value, and the app keeps the state object it
already had, so the other pages of the app still work.

## What it means

Every route receives the state and passes it onward through the
`Page` it returns. After each click, Drafter compares the type of the
state in the returned `Page` with the type of the previous state. The
`Page` your route returned carried a state of a different type, most
often `None`, so Drafter stopped the page before the wrong value
could reach your other routes.

## Where to look

The message names the route. Look at the first argument of every
`Page(...)` that route returns. The line after "The new value is" in
the technical message shows the value Drafter found there.

## Check

The type named in the message points to the cause:

- **A `Page` without state**: the message says the state "is a
  NoneType". `Page(["Score: 1"])` has a content list and no state, so
  its state is `None`. In an app that has state, every route returns
  `Page(state, [...])` with the state first.
- **One field in place of the whole state**: the message names the
  field's type, as in "is an int". `Page(state.score, [...])` passes a
  number where the state belongs.
- **The name `state` was reassigned**: a line such as
  `state = state.score + 1` replaces the state with a different
  value. Change the field (`state.score = state.score + 1`) and leave
  the name `state` alone.
- **The app started without a state**: the message ends "the
  previous state was a NoneType". The program calls `start_server()`
  with nothing in the parentheses, and a route then returns a `Page`
  that has a state. Give the starting state to `start_server`, as in
  `start_server(State(0))`.
- **`True` or `False` where a number belongs**: the message says the
  state "is a bool, but the previous state was an int". Python counts
  `True` and `False` as kinds of whole number, but Drafter compares
  the exact type, so an app whose state is a number cannot return
  `Page(state > 0, [...])`.
- **A class that inherits from your state class**: the message names
  the two classes. The exact type must match, so a state built from a
  subclass of `State` does not count as a `State`.

### A warning about the state's type

A route that returns a state of a different type always gets the
error page above. The debug panel can also list a warning about the
state's type when the state was replaced some other way, for example
by loading a saved state that holds a different type of value. The
Current tab of the debug panel then shows a line like this one under
"Errors & Warnings", and the line stays there as you move to other
pages:

```text
The site state changed from int to State; the state should keep the
same type for the whole site.
```

Reload the browser tab to start again from the state given to
`start_server`, and save a new copy of the state from the current
version of your program.

## Fix

Pass the state to the returned `Page`. You can change its fields,
but it should remain the same object and type:

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

Click the same button again. The page appears where the error page
was, and the debug panel's Current tab shows your `State` with its
fields after every click. A test such as
`assert_state(gain(State(0)), State(1))` checks that the route still
passes a `State` onward.

## Prevent

One habit prevents this error. Every route takes `state` as its
first parameter and returns `Page(state, [...])` with the state
first. A route that has nothing to remember still passes the state
through unchanged.

## Understand

[State](../../concepts/state.md) explains how state flows from route
to page to the next route, and why the type must stay stable.
