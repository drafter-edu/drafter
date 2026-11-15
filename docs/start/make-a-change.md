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
loop you will use hundreds of times: **edit the code, save, and see the
change**. Then you will break the app on purpose, read the error, and
fix it. Knowing what breakage looks like when you cause it deliberately
makes it far less alarming when it happens by accident.

## What you need

- The counter app from [Build your first app](first-app.md), running on
  your computer.
- About ten minutes.

## Step 1: The edit, save, look loop

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

Run the program once, and leave it running. On your computer, the loop
is:

1. **Edit**: change something in the code.
2. **Save** the file.
3. **Look**: the site in your browser reloads with your change.

While your program is running, Drafter watches the file. Each time you
save, Drafter restarts the site in the browser tab with the new code, so
you do not need to stop the program and run it again. The restart also
sets the state back to its starting value, which is why the count
returns to 0 after every save.

Try it now: change `"Current count: "` to a message of your own and
save. Switch to the browser tab, and the page shows your text. That
round trip is the rhythm you will follow whenever you build with
Drafter.

If you stopped the program or closed the editor, the site has nothing
to reload it. Run the file again to start it.

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

Save. When the page tries to display, Drafter stops it and shows an
error page that begins like this:

```text
Button Points to a Missing Page

The button labeled '+10' tries to go to a page named `ad_ten`, but your site has no route with that name.

payload.verification_failed: Payload verification failed for the page 'index': While verifying the Page() object returned from index, an error was encountered:
Button `+10` points to non-existent page `ad_ten`.
```

Read it slowly. The large title at the top names the kind of problem,
and the sentence under it says what happened in plain words: the `+10`
button points to a page called `ad_ten`, and no route with that name
exists. Below that sentence is the technical message, and below that
is a list titled "What To Try Next".

Drafter checks every link and button on a page before showing it, so a
broken app tells you what went wrong instead of showing a blank screen or
a dead button.

## Step 4: Undo it

Fix the spelling back to `add_ten` and save. The app works again.

That is the full recovery loop: **read the error, find the line, fix it,
save again**. If an error ever stumps you, the
[error index](../help/errors/index.md) explains the common ones in plain
language. You can look an error up there by the title at the top of the
error page, or search the docs for the exact text of the message.

## Common problems

- **You saved but nothing changed**: check that the program is still
  running, and that you edited the same file you are running. If the
  program has stopped, run it again.
- **A box says your code has a syntax error**: Drafter could not read
  the file you saved, so it kept showing the last version that worked.
  Fix the line the box names and save again.
- **The site still shows an old version**: stop the program and run it
  again, and use the browser tab that the new run opens. A fresh run
  always reflects the current code. A tab left open from an earlier
  run reloads by itself once the new run is going, unless it has
  waited more than two minutes and shows a box titled
  "Disconnected". Reload a tab that shows that box.
- **You cannot find the broken spot**: the last line of the error message
  names what is wrong (here, the button label and the missing page name).
  Search your file for that name; do not start reading from the top.

## Name it

- The rhythm you practiced is the **edit, save, look loop**. Drafter
  reloading the site each time you save is called **live reload**.
- The error you caused is a **link verification error**: before showing a
  page, Drafter checks that every button and link points to a route that
  actually exists.

## Make it yours

1. Add a `-10` button, first predicting what will happen if you click it
   enough times.
2. Break the app a different way: remove the closing bracket of the
   content list, save, and read the message that appears. Then fix it.

## Next steps

<div class="grid cards" markdown>

- **Next: See inside your app**

    ---

    Your app has been keeping records the whole time. The debug panel
    shows you state, history, and test results.

    [See inside your app](debug-panel.md)

</div>
