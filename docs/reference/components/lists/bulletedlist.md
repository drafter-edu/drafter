---
page_type: component
title: BulletedList
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - BulletedList
outcome: Show an unordered list from a Python list.
---

# BulletedList

Group: [Lists](../index.md#lists)

## Description

A `BulletedList` turns a Python list into a bulleted list on the page,
one bullet per item. It is the usual way to show a collection from
your state when order does not matter.

## Syntax

```python
BulletedList(items)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `items` | `list` | required | One entry per bullet. Items can be strings or components; each gets its own line automatically. |

Like every component, `BulletedList` also accepts
[styling and attribute keywords](../../keyword-attributes.md).

## Examples

A list straight from state, growing as the visitor adds to it:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    supplies: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Expedition Supplies"),
        BulletedList(state.supplies),
        "Add an item:",
        TextBox("item"),
        "\n",
        Button("Pack it", "pack")
    ])


@route
def pack(state: State, item: str) -> Page:
    state.supplies.append(item)
    return index(state)


start_server(State(["rope", "lantern"]))
```

## Notes

- Items that are not strings need converting first: build a list of
  strings with a loop (`for pet in state.pets:` ... `names.append(pet.name)`)
  and pass that. For rows of structured data, a
  [Table](../data/table.md) is usually clearer.
- An empty list renders as nothing at all. If "nothing" deserves an
  explanation, use an `if` in your route to show a message like
  `"Nothing packed yet.\n"` instead of the empty list.
- In tests, compare structurally:
  `assert_has(index(State(["rope"])), BulletedList(["rope"]))`.

## Related components

- [NumberedList](numberedlist.md): when order matters.
- [Table](../data/table.md): rows with multiple columns.
- [DefinitionList](definitionlist.md): term and definition pairs.

## External links

- [The ul element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/ul)
