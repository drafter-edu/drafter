---
page_type: component
title: DateInput
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - DateInput
outcome: Collect a date.
---

# DateInput

Group: [Input](../index.md#input)

## Description

A `DateInput` shows the browser's date picker. The visitor picks a
day from a small calendar, and the chosen date arrives at the route
as a parameter with the field's name. Use it whenever you would
otherwise ask people to type a date into a
[TextBox](textbox.md): the picker cannot produce a misspelled month
or an impossible day.

## Syntax

```python
DateInput(name)
DateInput(name, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `default_value` | `str` or `datetime.date` | empty | The pre-filled date, written as `"YYYY-MM-DD"` (like `"2026-07-27"`) or given as a `date` object. |

## Examples

The route's parameter is annotated as `datetime.date`, so Drafter
converts the submitted text into a real `date` object with fields
like `.year` and `.month`:

```python drafter height=280
from drafter import *
from dataclasses import dataclass
from datetime import date


@dataclass
class State:
    checkup: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Vet Visit Planner"),
        "Ada's next checkup: " + state.checkup + "\n",
        "Pick a day:",
        DateInput("day", state.checkup),
        "\n",
        Button("Schedule", "schedule")
    ])


@route
def schedule(state: State, day: date) -> Page:
    state.checkup = day.isoformat()
    return index(state)


start_server(State("2026-08-15"))
```

## Notes

- Annotate the receiving parameter as `datetime.date` to get a date
  object, or as `str` to get the raw `"YYYY-MM-DD"` text.
- With a `date` annotation, leaving the field empty submits today's
  date. With a `str` annotation, an empty field arrives as `""`.
- The browser controls what the picker looks like, so it differs
  between computers and phones; the submitted value is always in
  `"YYYY-MM-DD"` form regardless.
- A `default_value` that is not in `"YYYY-MM-DD"` form will not
  pre-fill the field; the browser silently shows it empty instead.

## Accessibility

Put a short label right before the field (the "Pick a day:" text
above, or a [Label](label.md)) so it is clear what the date is for.

## Related components

- [TimeInput](timeinput.md): collect a time of day instead.
- [DateTimeInput](datetimeinput.md): collect a date and time
  together.

## External links

- [The date input on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date)
