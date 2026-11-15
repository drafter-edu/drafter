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

Like every component, `DateInput` also accepts
[styling and attribute keywords](../../keyword-attributes.md). The
HTML attributes it recognizes as keywords are `min`, `max`, `step`,
`list`, `required`, `disabled`, `readonly`, and `autocomplete`.
(`list` takes the `id` of an HTML `<datalist>`, not a Python list.)
Drafter turns any other keyword it does not recognize into a CSS
style;
[Plain HTML attributes](../../keyword-attributes.md#plain-html-attributes)
explains that rule.

`min` and `max` limit the days the picker offers. Write them in the
same `"YYYY-MM-DD"` form as the default, as in
`DateInput("day", min="2026-08-01", max="2026-08-31")`. `step` is
counted in days. `disabled=True` and `readonly=True` both block
changes, and a disabled field's date is not sent to the route.

These limits apply to the picker only. Drafter does not ask the
browser to check the form when a button is clicked, so a date typed
outside the range, or an empty field marked `required=True`, still
reaches the route. Check the date inside the route.

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
- With a `date` annotation, leaving the field empty gives the route
  today's date. To tell an empty field apart from a chosen day,
  annotate the parameter as `date | None`, and an empty field gives
  `None`. A parameter with a default value receives its default. With
  a `str` annotation, an empty field arrives as `""`.
  [Blank values](../../route.md#blank-values) has the full rule.
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
