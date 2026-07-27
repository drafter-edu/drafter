---
page_type: component
title: DefinitionList
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - DefinitionList
outcome: Show term/definition pairs, including from dataclasses.
---

# DefinitionList

Group: [Lists](../index.md#lists)

## Description

A `DefinitionList` displays labeled facts: each entry is a term
with its definition indented beneath. Its best trick is
accepting a dataclass instance directly, turning field names
into terms and field values into definitions, which makes it the
one-line way to display a record. It also accepts a list of
(term, definition) pairs, or a dictionary.

## Syntax

```python
DefinitionList(a_dataclass_instance)
DefinitionList([("term", "definition"), ("term", "definition")])
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `items` | dataclass instance, list of pairs, or dict | required | The term/definition entries, in order. |

## Examples

One pet record, displayed without writing any display code:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    favorite_food: str
    naps_per_day: int


@dataclass
class State:
    resident: Pet


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet of the Month"),
        DefinitionList(state.resident)
    ])


start_server(State(Pet("Captain", "grey cat", "salmon", 14)))
```

## Notes

- With a dataclass, terms are the field names as written
  (`favorite_food`, underscores and all); for polished labels,
  build (term, definition) pairs instead.
- Pairs must have exactly two parts each; anything else stops
  the page with a friendly error naming the offending item.
- Definitions can be components, not only strings: a pair like
  `("Portrait", Image(state.photo))` works.
- For many records with the same fields, a
  [Table](../data/table.md) fits better; a definition list
  shines for one record at a time.

## Related components

- [Table](../data/table.md): rows of records.
- [BulletedList](bulletedlist.md): items without labels.

## External links

- [The dl element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dl)
