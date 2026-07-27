---
page_type: component
title: Table
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Table
outcome: Show rows of lists or dataclasses.
---

# Table

Group: [Data display](../index.md#data-display)

## Description

A `Table` renders rows and columns. Its favorite food is a list of
dataclasses: field names become the header row and each instance
becomes a row, which makes it the one-line display for exactly the
nested data most projects keep in state.

## Syntax

```python
Table(rows)
Table(rows, header)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `rows` | `list` | required | A list of dataclasses (header generated from fields), a list of lists (each inner list a row), or a single dataclass (rendered as field/value rows). |
| `header` | `list` | auto or none | Header cells, when you want different ones than the generated names. |

## Examples

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class Expedition:
    destination: str
    days: int
    survived: bool


@route
def index() -> Page:
    return Page([
        Header("Expedition Log"),
        Table([
            Expedition("the volcano", 3, True),
            Expedition("the couch", 1, True),
            Expedition("the DMV", 1, False)
        ]),
        Header("Same data, lists and a custom header", 2),
        Table([
            ["the volcano", 3],
            ["the couch", 1]
        ], ["Place", "Days"])
    ])


start_server()
```

## Notes

- Rows usually come straight from state
  (`Table(state.expeditions)`), so the table re-renders itself as
  the list grows; the [pet registry](../../../examples/pet-registry.md)
  is the worked example.
- Cell values render like page content: numbers need no `str()`
  here, and components can live in cells.
- In tests, match tables structurally:
  `assert_has(page, Table([Expedition("the couch", 1, True)]))`
  finds nothing when given a text needle, because text matching
  does not reach inside rows.
- An empty list renders an empty table; decide whether "no rows
  yet" deserves a message instead.

## Accessibility

Keep the header row honest (every column named) since screen
readers navigate cells by their column names; prefer one table per
kind of data over one mega-table.

## Related components

- [BulletedList](../lists/bulletedlist.md) and
  [NumberedList](../lists/numberedlist.md): one-column collections.
- [DefinitionList](../lists/definitionlist.md): one record's
  fields as term/value pairs.

## External links

- [The table element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/table)
