---
page_type: error
title: Page content must be a list of strings, numbers, booleans, or components
level: L1
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix invalid Page content.
error_text: "must be a list of strings, numbers, booleans, or components"
---

# Page content must be a list of strings, numbers, booleans, or components

## The error

```text
The content of a Page must be a list of strings, numbers, booleans, or components.
Found Pet instead.
```

The friendly version: "The content you returned in this Page was a
Pet, but it needs to be text, a number, a boolean, a component, or a
list of those." A related message appears when the list itself is
fine but one item inside it is not; that message names the route and
the offending item.

## What it means

A `Page` displays a list of strings, numbers, booleans, and
components. Something you put into that list, or in place of the
list itself, was none of those: perhaps a dataclass, a dictionary,
or a nested list. Drafter stopped rather than guess how to display
it.

## Where to look

Start with the route named in the message. Look at the `Page(...)`
call it returns and read the content list item by item.

## Check

- **A dataclass in the list**: `Page(state, [state.pet])`; show its
  fields (`state.pet.name`) or use a component like
  [Table](../../reference/components/data/table.md) built for
  structured data.
- **A nested list**: `Page(state, ["Pets:", state.names])` puts a
  whole list inside the content list. Join it into one string
  (`", ".join(state.names)`) or use
  [BulletedList](../../reference/components/lists/bulletedlist.md).
- **A dictionary in the list**: pull out the values you want to
  show, or hand the whole thing to a component built for it.
- **A missing comma**: two adjacent strings without a comma merge
  into one string, which Python allows, but a component next to a
  string without its comma is a syntax error that would appear
  before this one.

Plain numbers and booleans are fine on their own: `Page(state,
["Score:", state.score])` displays the score directly, no `str()`
needed.

## Fix

Keep everything inside one flat list of strings, numbers, booleans,
and components:

```python
@route
def index(state: State) -> Page:
    return Page(state, [
        "Score:",
        state.score,
        Button("Play", "play")
    ])
```

## Confirm

The page renders. A structural test pins it down:
`assert_has(index(State(3)), "3")`.

## Prevent

Keep the content list flat: helper functions that produce several
components should return a list you add with `+`, not nest as an
item. Structured values (dataclasses, dictionaries, lists) need to
be unpacked into their parts or given to a component that knows how
to display them.

## Understand

[Page](../../reference/page.md) documents exactly what content can
hold; [Routes and pages](../../concepts/routes-and-pages.md)
explains the underlying concept.
