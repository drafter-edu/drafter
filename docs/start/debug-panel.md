---
page_type: tutorial
title: See inside your app
level: L1
audience: S
priority: P0
prereqs: [start/make-a-change]
symbols: []
outcome: Read state, history, and test results in the debugger.
---

# See inside your app

## What you'll build

Still nothing new; something better. Below every Drafter app you run, there
is a **debug panel** that shows what your app is doing: the current state,
every page visit so far, and your test results. Learning to read it now
will save you hours later, because most "why is my app doing that?"
questions are answered by looking at it.

## What you need

- The counter app from the previous steps.
- About ten minutes.

## Step 1: Find the panel

Run this app, click the "debug" button in the top-right corner, and look below the page content:

```python drafter height=600
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    count: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current count: " + str(state.count) + "\n",
        Button("+1", "increment"),
        Button("Reset", "reset_count")
    ])


@route
def increment(state: State) -> Page:
    state.count = state.count + 1
    return index(state)


@route
def reset_count(state: State) -> Page:
    state.count = 0
    return index(state)


assert_state(increment(State(0)), State(1))
assert_state(reset_count(State(7)), State(0))

start_server(State(0))
```

The area under the page is the debug panel. It has five tabs. The two you
will use most often are:

- **Current** shows your state right now: every field of your `State`
  dataclass and its value. Click **+1** in the app above, then look at
  Current. The `count` field changed. Watching state change as you click
  is the fastest way to understand what your app is doing.
- **History** lists every page your app has shown, in order, with the
  state at each moment. If something went wrong three clicks ago, History
  lets you look back at exactly what happened.

The other three tabs, for when you need them:

- **Overview** lists all your routes and how they connect.
- **Tests** shows the results of your `assert_` lines. The two tests in
  this app appear there, marked as passing. Break one on your computer
  (change `State(1)` to `State(2)`) and watch it fail with an explanation
  of the difference.
- **Environment** shows files, packages, and configuration details.

## Step 2: See where print() goes

You can `print(...)` from inside a route to see what is happening while it
runs.

???+ note
    Not seeing anything print? You won't see printing in the browser version. You have to run this in Thonny!


Run this, click the button, and watch:



```python drafter height=430
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    count: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current count: " + str(state.count) + "\n",
        Button("Double it", "double_count")
    ])


@route
def double_count(state: State) -> Page:
    print("Before doubling:", state.count)
    state.count = state.count * 2
    print("After doubling:", state.count)
    return index(state)


start_server(State(1))
```

The printed lines appear in the app's console area rather than vanishing.
Printing the state before and after a change is the simplest debugging
tool you have, and it works everywhere.
[Print and the console](../help/printing-and-console.md) covers the
details.

## When the panel is missing

The debug panel exists to help the author, so it appears while you are
building. When you publish your finished app for others, the panel is
hidden. If you ever run your app and see no panel, it is in production
mode; nothing is wrong.

## Common problems

- **The panel shows an old state value**: state updates when a route runs.
  If you expected a change and Current does not show it, the route that
  should have changed it either did not run or did not assign the field.
  History will show which routes ran.
- **Your tests do not appear in the Tests tab**: `assert_` lines must run
  when your program starts, so put them after your routes are defined and
  before `start_server(...)`.
- **The panel is gone**: see above; the app is in production mode.

## Name it

- The area under your app is the **debug panel** (or debugger).
- The record of visited pages is the **page history**. Later, you will
  [turn history into regression tests](../add/freeze-pages.md)
  automatically.

## Make it yours

1. Add a third test to the counter that you predict will fail, run the
   app, and read the failure message in the Tests tab. Then fix the test.
2. Add a `print` to `index` and observe exactly when it runs. Every
   click? Only sometimes? What does that tell you?

## Next steps

<div class="grid cards" markdown>

- **Next: How Drafter works**

    ---

    You have built, broken, fixed, and inspected an app. Five minutes of
    naming what actually happened.

    [How Drafter works](how-drafter-works.md)

</div>
