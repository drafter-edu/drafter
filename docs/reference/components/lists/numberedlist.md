---
page_type: component
title: NumberedList
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - NumberedList
outcome: Show an ordered list.
---

# NumberedList

Group: [Lists](../index.md#lists)

## Description

A `NumberedList` turns a Python list into a numbered list on the
page, with one numbered line (1, 2, 3, ...) per entry. Use it when
the order matters, as it does for steps in a process, rankings, or
a queue.

## Syntax

```python
NumberedList(items)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `items` | `list` | required | One entry per numbered line. Items can be strings or components. |

Like every component, `NumberedList` also accepts
[styling and attribute keywords](../../keyword-attributes.md).

## Examples

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    queue: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Grooming Queue"),
        NumberedList(state.queue),
        Button("Groom the next pet", "next_pet")
    ])


@route
def next_pet(state: State) -> Page:
    if state.queue:
        state.queue.pop(0)
    return index(state)


start_server(State(["Ada", "Babbage", "Captain", "Domino"]))
```

## Notes

- The numbers come from each item's position, not from your data,
  so removing the first item renumbers the rest, as the example
  shows.
- In every other way, a `NumberedList` behaves like a
  [BulletedList](bulletedlist.md): structured items should be
  converted to strings with a loop, and an empty list renders as
  nothing.

## Related components

- [BulletedList](bulletedlist.md): shows the items with bullets,
  for when order does not matter.
- [Table](../data/table.md): displays rows with multiple columns.

## External links

- [The ol element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/ol)
