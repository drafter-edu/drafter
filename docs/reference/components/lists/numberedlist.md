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
page: 1, 2, 3, one item per entry. Use it when the order is the
point: steps, rankings, a queue.

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

- The numbers come from position, not from your data; removing the
  first item renumbers the rest, as the example shows.
- Everything else behaves like [BulletedList](bulletedlist.md):
  build strings with a loop for structured items, and an empty list
  renders as nothing.

## Related components

- [BulletedList](bulletedlist.md): when order does not matter.
- [Table](../data/table.md): rows with multiple columns.

## External links

- [The ol element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/ol)
