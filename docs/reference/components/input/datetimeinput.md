---
page_type: component
title: DateTimeInput
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - DateTimeInput
outcome: Collect a date and time.
---

# DateTimeInput

Group: [Input](../index.md#input)

## Description

A `DateTimeInput` shows the browser's combined date and time
picker. The visitor picks a day and a clock time in one field, and
the result arrives at the route as a parameter with the field's
name. Use it for things that happen at a specific moment, like an
appointment or a deadline; when you only need one half, use
[DateInput](dateinput.md) or [TimeInput](timeinput.md) instead.

## Syntax

```python
DateTimeInput(name)
DateTimeInput(name, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `default_value` | `str` or `datetime.datetime` | empty | The pre-filled moment, written as `"YYYY-MM-DDTHH:MM"` (like `"2026-07-27T14:30"`, with a capital T between the date and the time) or given as a `datetime` object. |

## Examples

The route's parameter is annotated as `datetime.datetime`, so
Drafter converts the submitted text into a `datetime` object with
fields like `.month`, `.day`, and `.hour`:

```python drafter height=280
from drafter import *
from dataclasses import dataclass
from datetime import datetime


@dataclass
class State:
    appointment: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Grooming Appointment"),
        "Babbage's next grooming: " + state.appointment + "\n",
        "Reschedule to:",
        DateTimeInput("moment", state.appointment),
        "\n",
        Button("Book it", "book")
    ])


@route
def book(state: State, moment: datetime) -> Page:
    state.appointment = moment.isoformat(timespec="minutes")
    return index(state)


start_server(State("2026-08-01T10:00"))
```

## Notes

- Annotate the receiving parameter as `datetime.datetime` to get a
  `datetime` object, or as `str` to get the raw
  `"YYYY-MM-DDTHH:MM"` text.
- With a `datetime` annotation, leaving the field empty submits the
  current date and time. With a `str` annotation, an empty field
  arrives as `""`.
- The `T` in the middle of the value is part of the standard
  format; `datetime.fromisoformat` and Drafter's conversion both
  expect it.
- There is no time zone in the value: it is whatever the visitor's
  computer considers local time.

## Accessibility

Put a short label right before the field (the "Reschedule to:" text
above, or a [Label](label.md)) so it is clear what moment is being
chosen.

## Related components

- [DateInput](dateinput.md): just the calendar date.
- [TimeInput](timeinput.md): just the clock time.

## External links

- [The datetime-local input on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/datetime-local)
