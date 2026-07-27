---
page_type: how-to
title: Build one working path
level: L2
audience: S
priority: P1
prereqs: [your-project/plan-your-data]
symbols: []
outcome: Get a thin end-to-end slice working first.
---

# Build one working path

## Goal

You want a version of your app that does one real thing, start to
finish, before any second feature exists. Developers call this a
*walking skeleton*: it has all the bones and none of the muscle,
but it already walks.

## Before you start

You have [sketches](sketch-the-pages.md) and a
[written State](plan-your-data.md). Pick the single most important
path through your sketches: for a tracker, "add an entry and see it
listed"; for a store, "buy one thing"; for a story, "make one
choice". You are not looking for the fanciest path, but for the
*load-bearing* one.

## Step 1: The skeleton file

Start every project the same way: the `State` dataclass from the
last step, an `index` route that shows almost nothing, and a call
to `start_server`.

```python drafter height=200
from drafter import *
from dataclasses import dataclass


@dataclass
class Entry:
    date: str
    distance_km: float
    note: str


@dataclass
class State:
    entries: list[Entry]
    goal_km: float


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Trail Tracker"),
        "Entries so far: " + str(len(state.entries))
    ])


start_server(State([], 100.0))
```

Run it. A boring page that runs beats a brilliant page that does
not exist, and from here every change is small.

## Step 2: One route at a time along the path

Add the chosen path's pages in the order a user would click through
them, and run the app after each addition. For the tracker path,
that means adding the add-entry form page, then the save route,
then the list display in `index`. Each addition is one route or one
component, and the app should run correctly after every one.

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class Entry:
    date: str
    distance_km: float
    note: str


@dataclass
class State:
    entries: list[Entry]
    goal_km: float


@route
def index(state: State) -> Page:
    lines = []
    for entry in state.entries:
        lines.append(entry.date + ": " + str(entry.distance_km) + " km")
    return Page(state, [
        Header("Trail Tracker"),
        BulletedList(lines),
        Button("Add a hike", "add_entry")
    ])


@route
def add_entry(state: State) -> Page:
    return Page(state, [
        Header("New hike"),
        "Date:",
        DateInput("date"),
        "\nDistance in km:",
        TextBox("distance", 5),
        "\nNote:",
        TextBox("note"),
        "\n",
        Button("Save", "save_entry"),
        Button("Cancel", "index")
    ])


@route
def save_entry(state: State, date: str, distance: float, note: str) -> Page:
    state.entries.append(Entry(date, distance, note))
    return index(state)


assert_state(
    save_entry(State([], 100.0), "2026-07-27", 8.5, "with Babbage"),
    State([Entry("2026-07-27", 8.5, "with Babbage")], 100.0))

start_server(State([], 100.0))
```

That is a complete walking skeleton: one path, one test, and
everything else still missing on purpose. Notice what it does *not*
have: no goal progress, no way to delete an entry, no styling.
Those are features, and features come later,
[one at a time](add-features.md).

## Step 3: Prove it end to end

Click the whole path like a stranger would, and write one test for
its central rule (the `assert_state` above). This is also the
moment to make your first commit, or at least to save a copy of
the working file. Every later experiment deserves a known-good
version to fall back to.

## Common problems

- **Building all pages before any path**: five beautiful but
  disconnected pages make a worse demo than two connected ones. Go
  deep first, then broad.
- **The slice keeps widening**: "while I'm in here, I'll add
  categories" is how walking skeletons stall. Write the tempting
  feature on your stretch list and stay on the path.
- **Stuck on one route for an hour**: shrink the goal. Make the
  route return a hard-coded page, get the click working, and then
  make the page real. Progress matters more than polish at this
  stage.
- **The plan changed once you started building**: that is normal
  and expected. Update the sketch and the `State`; they are cheap
  to change, which is exactly why they are paper and one dataclass
  rather than finished code.

## You are ready for the next step when

You can click through the whole path, one test pins down its
central rule, and a saved working copy exists. Then grow the app
with [Add features one at a time](add-features.md), and keep
[writing tests](test-as-you-go.md) as you go.
