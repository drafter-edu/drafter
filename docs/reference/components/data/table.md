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

A `Table` renders rows and columns. It works best with a list of
dataclasses: the field names become the header row, and each
instance becomes a row of the table. Since most projects keep
exactly this kind of nested data in state, a `Table` can often
display it with a single line of code.

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
  (`Table(state.expeditions)`), so the table reflects the list each
  time the page renders; the
  [pet registry](../../../examples/pet-registry.md) shows this
  pattern in a complete project.
- Cell values render the same way page content does: numbers do not
  need `str()`, and cells can contain components.
- In tests, match tables structurally:
  `assert_has(page, Table([Expedition("the couch", 1, True)]))`.
  Searching for the cell text instead finds nothing, because text
  matching does not reach inside rows.
- An empty list renders as an empty table; consider whether your
  page should show a message instead when there are no rows yet.

## Accessibility

Name every column in the header row, since screen readers navigate
cells by their column names. Prefer one table per kind of data over
a single large table that mixes several kinds.

## Related components

- [BulletedList](../lists/bulletedlist.md) and
  [NumberedList](../lists/numberedlist.md): lists for displaying
  one-column collections.
- [DefinitionList](../lists/definitionlist.md): displays one
  record's fields as term/value pairs.

## External links

- [The table element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/table)
