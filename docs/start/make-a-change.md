---
page_type: tutorial
title: Make one visible change
level: L1
audience: S
priority: P0
prereqs: [start/first-app]
symbols: []
outcome: Edit a running app, see the result, and recover from a first error.
---

# Make one visible change

## What you'll build

This step adds nothing new to the app. Instead, you will practice the
loop you will use hundreds of times: **edit the code, save, reload, see
the change**. Then you will break the app on purpose, read the error, and
fix it. Knowing what breakage looks like when you cause it deliberately
makes it far less alarming when it happens by accident.

## What you need

- The counter app from [Build your first app](first-app.md), running on
  your computer.
- About ten minutes.

## Step 1: The edit, save, reload loop

Here is the counter again as a starting point:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    count: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current count: " + str(state.count) + "\n",
        Button("+1", "increment")
    ])


@route
def increment(state: State) -> Page:
    state.count = state.count + 1
    return index(state)


start_server(State(0))
```

On your computer, the loop is:

1. **Edit**: change something in the code.
2. **Save and run** the file again.
3. **Look**: the site reloads with your change.

Try it now: change `"Current count: "` to a message of your own, save, and
run. The page shows your text. That round trip is the rhythm you will
follow whenever you build with Drafter.

## Step 2: Add a second button

Make a slightly bigger change: add a `+10` button. That takes two edits, a
new route and a new `Button` pointing at it:

```python drafter height=260
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
        Button("+10", "add_ten")
    ])


@route
def increment(state: State) -> Page:
    state.count = state.count + 1
    return index(state)


@route
def add_ten(state: State) -> Page:
    state.count = state.count + 10
    return index(state)


start_server(State(0))
```

**Predict first**: what happens if you add the `Button("+10", "add_ten")`
line but forget to write the `"add_ten"` function? Hold that thought; you are
about to find out.

## Step 3: Break it on purpose

In your copy, misspell the function name inside the button, like this:

```python
Button("+10", "ad_ten")
```

Save and run. When the page tries to display, Drafter stops it and shows
an error like:

```text
Problem Displaying This Page
Drafter could not turn your page result into something it can display.

payload.verification_failed: Payload verification failed for URL index: While verifying the Page() object returned from index, an error was encountered:
Link `+10` points to non-existent page `ad_ten`.  
```

Read it slowly. The last line names the exact problem: the `+10` button
points to a page called `ad_ten`, and no route with that name exists.
Drafter checks every link and button on a page before showing it, so a
broken app tells you what went wrong instead of showing a blank screen or
a dead button.

## Step 4: Undo it

Fix the spelling back to `add_ten`, save, and run. The app works again.

That is the full recovery loop: **read the error, find the line, fix it,
run again**. If an error ever stumps you, the
[error index](../help/errors/index.md) explains the common ones in plain
language; you can search it with the exact text of your error message.

## Common problems

- **You saved but nothing changed**: make sure you ran the file again
  after saving, and that you edited the same file you are running.
- **The site shows an old version**: stop the program and run it again; a
  fresh run always reflects the current code.
- **You cannot find the broken spot**: the last line of the error message
  names what is wrong (here, the button label and the missing page name).
  Search your file for that name; do not start reading from the top.

## Name it

- The rhythm you practiced is the **edit, save, reload loop**.
- The error you caused is a **link verification error**: before showing a
  page, Drafter checks that every button and link points to a route that
  actually exists.

## Make it yours

1. Add a `-10` button, first predicting what will happen if you click it
   enough times.
2. Break the app a different way: remove the closing bracket of the
   content list, run it, and read that error too. Then fix it.

## Next steps

<div class="grid cards" markdown>

- **Next: See inside your app**

    ---

    Your app has been keeping records the whole time. The debug panel
    shows you state, history, and test results.

    [See inside your app](debug-panel.md)

</div>
