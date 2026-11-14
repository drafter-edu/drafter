---
page_type: component
title: CheckBox
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - CheckBox
outcome: Collect a yes/no.
---

# CheckBox

Group: [Input](../index.md#input)

## Description

A `CheckBox` collects a yes/no answer. The receiving route's parameter
should be annotated `bool`: the value arrives as `True` when the box
is checked and `False` when it is not, including when the visitor
leaves the box untouched.

## Syntax

```python
CheckBox(name)
CheckBox(name, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. Must be a valid Python parameter name. |
| `default_value` | `bool` | `False` | Whether the box starts checked. |

Like every component, `CheckBox` also accepts
[styling and attribute keywords](../../keyword-attributes.md). It
recognizes no HTML attributes beyond the ones every component shares,
so `disabled=True` and `required=True` do not work here. Drafter turns
a keyword it does not recognize into a CSS style, which the browser
ignores, and it reports no error.
[Plain HTML attributes](../../keyword-attributes.md#plain-html-attributes)
explains the keyword rule.

## Examples

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    walked: bool
    fed: bool


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Babbage's Day"),
        "Walked: " + str(state.walked) + "\n",
        "Fed: " + str(state.fed) + "\n",
        CheckBox("walked_today", state.walked),
        " Took Babbage for a walk\n",
        CheckBox("fed_today", state.fed),
        " Fed Babbage\n",
        Button("Save", "save")
    ])


@route
def save(state: State, walked_today: bool, fed_today: bool) -> Page:
    state.walked = walked_today
    state.fed = fed_today
    return index(state)


start_server(State(False, False))
```

## Notes

- An unchecked box still submits a value: the parameter receives
  `False`, not nothing. (Behind the scenes, Drafter adds a hidden
  companion field so the unchecked state is submitted too.)
- Passing the current state value as `default_value` keeps the box
  reflecting what was last saved, as in the example.
- For choosing one option among several, use
  [RadioButtonGroup](radiobuttongroup.md) or
  [SelectBox](selectbox.md); for choosing several from a list, use
  [RelatedCheckBox](relatedcheckbox.md).

## Accessibility

Put the describing text directly next to the box, as in the example,
or use a [Label](label.md) associated with the box so clicking the
words toggles it.

## Related components

- [RelatedCheckBox](relatedcheckbox.md): many related yes/nos,
  received as one list.
- [RadioButtonGroup](radiobuttongroup.md): choose exactly one option
  instead.
- [Ask the user for information](../../../add/ask-for-information.md)
  is the how-to guide, with a recipe that puts a checkbox in a form.

## External links

- [The input checkbox type on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/checkbox)
