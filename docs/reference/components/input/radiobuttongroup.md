---
page_type: component
title: RadioButtonGroup
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - RadioButtonGroup
outcome: Choose one option with all options visible.
---

# RadioButtonGroup

Group: [Input](../index.md#input)

## Description

A `RadioButtonGroup` shows every option with a round button beside
it; the visitor picks exactly one, and the chosen text arrives at
the route under the group's name. It is a
[SelectBox](selectbox.md) with everything on display: better when
options are few and comparing them matters.

## Syntax

```python
RadioButtonGroup(name, options)
RadioButtonGroup(name, options, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `options` | `list[str]` | required | The choices, each rendered with its own radio button. |
| `default_value` | `str` | none chosen | The option pre-selected when the page loads. |

## Examples

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    roast: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Marshmallow Station"),
        "Current roast: " + state.roast + "\n",
        RadioButtonGroup("level",
                         ["barely warm", "golden", "on fire"],
                         state.roast),
        "\n",
        Button("Roast", "roast_it")
    ])


@route
def roast_it(state: State, level: str) -> Page:
    state.roast = level
    return index(state)


start_server(State("golden"))
```

## Notes

- With no `default_value`, nothing starts selected, and a visitor
  can submit without choosing; give a default when the parameter
  has no default of its own.
- Radio buttons are for choices that are genuinely exclusive; if
  choosing several should be legal, that is
  [RelatedCheckBox](relatedcheckbox.md).
- More than five or six options starts crowding a page; that is the
  signal to switch to a [SelectBox](selectbox.md).

## Accessibility

The group renders each option labeled, so clicking an option's text
selects it. Introduce the group with a visible question ("Current
roast:") so its purpose is announced, not inferred.

## Related components

- [SelectBox](selectbox.md): the compact form of the same choice.
- [CheckBox](checkbox.md): a single yes/no instead.

## External links

- [The input radio type on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/radio)
