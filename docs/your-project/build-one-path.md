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
finish, before any second feature exists. Builders call this a
*walking skeleton*: all the bones, none of the muscle, and it
already walks.

## Before you start

You have [sketches](sketch-the-pages.md) and a
[written State](plan-your-data.md). Pick the single most important
path through your sketches: for a tracker, "add an entry and see it
listed"; for a store, "buy one thing"; for a story, "make one
choice". Not the fanciest path, the *load-bearing* one.

## Step 1: The skeleton file

Start every project the same way: `State` (from the last step), an
`index` route showing almost nothing, and `start_server`.

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

Add the chosen path's pages in click order, running after each.
For the tracker path that means: the add-entry form page, then the
save route, then making `index` show the list. Each addition is one
route or one component, and the app runs between every pair.

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

That is a complete walking skeleton: one path, one test, everything
else still missing on purpose. Notice what it is *not*: no goal
progress, no deleting, no styling. Those are features, and features
come [one at a time](add-features.md), later.

## Step 3: Prove it end to end

Click the whole path like a stranger would, and write one test for
its central rule (the `assert_state` above). This is also the
moment to make your first commit, or at least a copy of the file
that works; every later experiment deserves a safe floor to fall
back to.

## Common problems

- **Building all pages before any path**: five beautiful
  disconnected pages demo worse than two connected ones. Depth
  first, then breadth.
- **The slice keeps widening**: "while I'm in here I'll add
  categories" is how skeletons die. Write the temptation on your
  stretch list and stay on the path.
- **Stuck on one route for an hour**: shrink the ambition: make
  the route return a hard-coded page, get the click working, then
  make it real. Motion beats polish at this stage.
- **The plan survived contact and changed**: fine, expected, and
  cheap: update the sketch and the `State`, which is exactly why
  they are paper and one dataclass rather than finished code.

## You are ready for the next step when

The path works by clicking, one test pins its rule, and a safe
copy exists. Then grow it with
[Add features one at a time](add-features.md), keeping
[tests coming](test-as-you-go.md) as you go.
