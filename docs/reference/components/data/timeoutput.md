---
page_type: component
title: TimeOutput
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - TimeOutput
outcome: Show semantic timestamps.
---

# TimeOutput

Group: [Data display](../index.md#data-display)

## Description

A `TimeOutput` displays a date or time the human way ("July
25th") while carrying the precise machine-readable form
("2026-07-25") invisibly alongside. Search engines, calendars,
and assistive tools read the precise form; your visitors read
yours. It displays as plain inline text.

## Syntax

```python
TimeOutput(text, datetime="2026-07-25")
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `*content` | strings or components | required | The human-readable version. |
| `datetime` | `str`, or a `date`/`time`/`datetime` object | none | The machine-readable form, as ISO text (`"2026-07-25"`, `"14:30"`) or an object that converts itself. |

## Examples

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adoption Fair"),
        Paragraph(
            "Meet the pets on ",
            TimeOutput("Saturday the 25th", datetime="2026-07-25"),
            " starting at ",
            TimeOutput("2 in the afternoon", datetime="14:00"),
            "."
        )
    ])


start_server(State())
```

## Notes

- Values from a [DateInput](../input/dateinput.md) family field
  are already in ISO form, so they can pass straight through as
  the `datetime` argument while your route formats the friendly
  version.
- A `datetime.date`, `time`, or `datetime` object handed to the
  keyword converts itself to ISO text automatically.
- Without the `datetime` keyword the component still renders,
  but then it adds nothing over plain text; the keyword is the
  point.

## Related components

- [DateInput](../input/dateinput.md), [TimeInput](../input/timeinput.md),
  and [DateTimeInput](../input/datetimeinput.md): where
  machine-readable date and time values come from.

## External links

- [The time element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/time)
