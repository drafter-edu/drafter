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
caption when the input is reached. A plain string before an input
works well in early projects; a `Label` is the more polished
choice.

## Syntax

```python
Label(text, for_id)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `text` | `str` | required | The caption text. |
| `for_id` | `str` or a form component | `None` | The input the label belongs to: an element id, or the component object itself, which is the more convenient form. |

## Examples

Passing the component itself attaches the label without your having
to invent an id:

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

Click the words "I agree to water the plants" and the checkbox
toggles.

## Notes

- Build the input first, store it in a variable, and pass that
  variable to both the `Label` and the content list, as above; the
  label reads the input's id from the object.
- A label with no `for_id` renders as ordinary styled text;
  attaching it to an input is what provides the benefits described
  above.

## Accessibility

A `Label` exists for accessibility: prefer one over a bare string
for any input a stranger will use, and keep the label text short
and specific.

## Related components

- [TextBox](textbox.md), [CheckBox](checkbox.md),
  [SelectBox](selectbox.md): inputs a label can attach to.

## External links

- [The label element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/label)
