---
page_type: component
title: TimeInput
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - TimeInput
outcome: Collect a time.
---

# TimeInput

Group: [Input](../index.md#input)

## Description

A `TimeInput` shows the browser's time picker. The visitor picks a
time of day (hours and minutes), and the chosen time arrives at the
route as a parameter with the field's name. Use it instead of a
[TextBox](textbox.md) whenever you need a clock time: the picker
cannot produce a 25th hour or a stray letter.

## Syntax

```python
TimeInput(name)
TimeInput(name, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `default_value` | `str` or `datetime.time` | empty | The pre-filled time, written as `"HH:MM"` in 24-hour form (like `"14:30"`) or given as a `time` object. |

Like every component, `TimeInput` also accepts
[styling and attribute keywords](../../keyword-attributes.md). The
HTML attributes it recognizes as keywords are `min`, `max`, `step`,
`list`, `required`, `disabled`, `readonly`, and `autocomplete`.
(`list` takes the `id` of an HTML `<datalist>`, not a Python list.)
Drafter turns any other keyword it does not recognize into a CSS
style;
[Plain HTML attributes](../../keyword-attributes.md#plain-html-attributes)
explains that rule.

`min` and `max` limit the times the picker offers. Write them in the
same `"HH:MM"` form as the default, as in
`TimeInput("when", min="09:00", max="17:00")`. `step` is counted in
seconds, so `step=900` moves in quarter hours. `disabled=True` and
`readonly=True` both block changes, and a disabled field's time is
not sent to the route.

These limits apply to the picker only. Drafter does not ask the
browser to check the form when a button is clicked, so a time typed
outside the range, or an empty field marked `required=True`, still
reaches the route. Check the time inside the route.

## Examples

The route's parameter is annotated as `datetime.time`, so Drafter
converts the submitted text into a real `time` object with `.hour`
and `.minute` fields:

```python drafter height=280
from drafter import *
from dataclasses import dataclass
from datetime import time


@dataclass
class State:
    dinner: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Cat Feeding Schedule"),
        "Captain eats dinner at: " + state.dinner + "\n",
        "New dinner time:",
        TimeInput("when", state.dinner),
        "\n",
        Button("Update", "update")
    ])


@route
def update(state: State, when: time) -> Page:
    state.dinner = when.isoformat(timespec="minutes")
    return index(state)


start_server(State("17:00"))
```

## Notes

- Annotate the receiving parameter as `datetime.time` to get a time
  object, or as `str` to get the raw `"HH:MM"` text.
- With a `time` annotation, leaving the field empty gives the route
  the current time. To tell an empty field apart from a chosen time,
  annotate the parameter as `time | None`, and an empty field gives
  `None`. A parameter with a default value receives its default. With
  a `str` annotation, an empty field arrives as `""`.
  [Blank values](../../route.md#blank-values) has the full rule.
- Values always use 24-hour form (`"14:30"`, not `"2:30 PM"`), even
  when the picker displays AM and PM to the visitor.

## Accessibility

Put a short label right before the field (the "New dinner time:"
text above, or a [Label](label.md)) so it is clear what the time is
for.

## Related components

- [DateInput](dateinput.md): collect a calendar date instead.
- [DateTimeInput](datetimeinput.md): collect a date and time
  together.

## External links

- [The time input on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/time)
