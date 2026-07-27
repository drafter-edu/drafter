---
page_type: component
title: RelatedCheckBox
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - RelatedCheckBox
outcome: Choose many options, received as a list parameter.
---

# RelatedCheckBox

Group: [Input](../index.md#input)

## Description

`RelatedCheckBox`es are checkboxes that belong together: they share
one name, and the values of all the checked boxes arrive at the
route as a single list parameter. Use them when the visitor may
choose any number of options; for a single yes/no answer, use a
plain [CheckBox](checkbox.md).

## Syntax

```python
RelatedCheckBox(name, value)
RelatedCheckBox(name, value, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The shared group name, matching one route parameter annotated `list[str]`. |
| `value` | `str` | required | What this box contributes to the list when checked. |
| `default_value` | `bool` | `False` | Whether this box starts checked. |

## Examples

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    toppings: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Sundae Builder"),
        "Current toppings:",
        BulletedList(state.toppings),
        RelatedCheckBox("picks", "sprinkles"),
        " sprinkles\n",
        RelatedCheckBox("picks", "cherries"),
        " cherries\n",
        RelatedCheckBox("picks", "regret"),
        " regret\n",
        Button("Build it", "build")
    ])


@route
def build(state: State, picks: list[str]) -> Page:
    state.toppings = picks
    return index(state)


start_server(State([]))
```

## Notes

- The receiving parameter should be annotated `list[str]`; with
  nothing checked it receives an empty list, not an error.
- The group is deliberately exempt from the
  [duplicate-name rule](../../../help/errors/duplicate-component-name.md),
  because sharing one name is exactly how the boxes form a group.
- The list records which values were checked, not the order in
  which the visitor clicked them.

## Accessibility

Put each box's describing text directly beside it, as in the
example, and introduce the group with a heading or question so its
collective purpose is clear.

## Related components

- [CheckBox](checkbox.md): one independent yes/no.
- [RadioButtonGroup](radiobuttongroup.md): choose exactly one
  instead.

## External links

- [The input checkbox type on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/checkbox)
