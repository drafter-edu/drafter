---
page_type: component
title: Label
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Label
outcome: Caption an input accessibly.
---

# Label

Group: [Input](../index.md#input)

## Description

A `Label` is a caption formally attached to an input. Attached
labels do two things plain strings cannot: clicking the label
focuses (or toggles) its input, and screen readers announce the
caption when the input is reached. Plain strings before inputs are
fine for early projects; labels are the polished version.

## Syntax

```python
Label(text, for_id)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `text` | `str` | required | The caption text. |
| `for_id` | `str` or a form component | `None` | What the label belongs to: an element id, or the component itself, which is the convenient form. |

## Examples

Passing the component itself wires the connection without inventing
ids:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    signed_up: bool


@route
def index(state: State) -> Page:
    agree_box = CheckBox("agrees")
    name_box = TextBox("volunteer")
    return Page(state, [
        Header("Volunteer Sign-up"),
        Label("Your name:", name_box),
        name_box,
        "\n",
        agree_box,
        Label(" I agree to water the plants", agree_box),
        "\n",
        Button("Sign up", "sign")
    ])


@route
def sign(state: State, volunteer: str, agrees: bool) -> Page:
    state.signed_up = agrees
    return index(state)


start_server(State(False))
```

Click the words "I agree to water the plants": the checkbox
toggles.

## Notes

- Build the input first, store it in a variable, and pass that
  variable to both the `Label` and the content list, as above; the
  label reads the input's id from the object.
- A label with no `for_id` is just styled text; the connection is
  the point.

## Accessibility

This component *is* the accessibility feature: prefer a `Label`
over a bare string for any input a stranger will use, and keep
label text short and specific.

## Related components

- [TextBox](textbox.md), [CheckBox](checkbox.md),
  [SelectBox](selectbox.md): the things labels attach to.

## External links

- [The label element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/label)
