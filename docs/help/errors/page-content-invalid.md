---
page_type: error
title: Page content must be a list of strings or components
level: L1
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix invalid Page content.
error_text: "must be a list of strings or components"
---

# Page content must be a list of strings or components

## The error

```text
The content of a Page must be a list of strings or components.
Found int instead.
```

The friendly version: "The content you returned in this Page was an
int, but it needs to be text, a component, or a list of those." A
related message appears when the list itself is fine but one item
inside it is not; that message names the route and the offending
item.

## What it means

A `Page` displays a list of strings and components. Something you
put into that list, or in place of the list itself, was neither a
string nor a component: perhaps a number, a dataclass, or a nested
list. Drafter stopped rather than guess how to display it.

## Where to look

Start with the route named in the message. Look at the `Page(...)`
call it returns and read the content list item by item.

## Check

- **A bare value**: `Page(state, state.score)` passes a number where
  the content list belongs. Content must be a list.
- **A number in the list**: `Page(state, ["Score:", state.score])`;
  every non-text value needs `str()` around it.
- **A dataclass in the list**: `Page(state, [state.pet])`; show its
  fields (`state.pet.name`) or use a component like
  [Table](../../reference/components/data/table.md) built for
  structured data.
- **A missing comma**: two adjacent strings without a comma merge
  into one string, which Python allows, but a component next to a
  string without its comma is a syntax error that would appear
  before this one.

## Fix

Convert values to strings and keep everything inside one flat list:

```python
@route
def index(state: State) -> Page:
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        Button("Play", "play")
    ])
```

## Confirm

The page renders. A structural test pins it down:
`assert_has(index(State(3)), "Score: 3")`.

## Prevent

Get in the habit of wrapping `str()` around any number or other
value that goes into page content, and keep the content list flat:
helper functions that produce several components should return a
list you add with `+`, not nest as an item.

## Understand

[Page](../../reference/page.md) documents exactly what content can
hold; [Routes and pages](../../concepts/routes-and-pages.md)
explains the underlying concept.
