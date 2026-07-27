---
page_type: component
title: SelectBox
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - SelectBox
outcome: Choose one option from a list.
---

# SelectBox

Group: [Input](../index.md#input)

## Description

A `SelectBox` is a dropdown menu. The visitor picks exactly one
option from a list you define, and the chosen option's text arrives
at the route as a parameter with the box's name. Use it when there
are many options or little room on the page; when all the options
should be visible at once, use a
[RadioButtonGroup](radiobuttongroup.md).

## Syntax

```python
SelectBox(name, options)
SelectBox(name, options, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `options` | `list[str]` | required | The choices, shown in order. Non-string values are converted to text. |
| `default_value` | `str` | first option | The pre-chosen option. Must be one of the options, or the page stops with a [friendly error](../../../help/errors/selectbox-default-missing.md). |
| `allow_missing` | `bool` | `False` | Skip the default-must-be-an-option check. Rarely wanted. |

## Examples

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    destination: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Trip Planner"),
        "Current destination: " + state.destination + "\n",
        SelectBox("choice",
                  ["aquarium", "museum", "volcano", "library"],
                  state.destination),
        "\n",
        Button("Choose", "choose")
    ])


@route
def choose(state: State, choice: str) -> Page:
    state.destination = choice
    return index(state)


start_server(State("aquarium"))
```

## Notes

- The route always receives one of the option strings, which makes
  `SelectBox` the input least in need of validation: the visitor
  cannot type something unexpected.
- Passing the current state value as the default, as above, keeps
  the box showing what was last chosen.
- Each option is both the display text and the submitted value.
  `SelectBox` cannot show one label while sending a different code;
  if you need that, receive the label and look up the matching code
  inside the route.

## Accessibility

Give the box a visible label (the "Current destination:" text or a
[Label](label.md)); without one, the dropdown's purpose is unclear
to everyone, and especially to screen-reader users.

## Related components

- [RadioButtonGroup](radiobuttongroup.md): the same kind of choice
  with all options visible.
- [RelatedCheckBox](relatedcheckbox.md): choose several options
  instead.

## External links

- [The select element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/select)
