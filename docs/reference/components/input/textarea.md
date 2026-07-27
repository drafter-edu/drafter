---
page_type: component
title: TextArea
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - TextArea
outcome: Collect multi-line text.
---

# TextArea

Group: [Input](../index.md#input)

## Description

A `TextArea` collects multiple lines of typed text: a poem, a review,
a story. It works exactly like a [TextBox](textbox.md), delivering its
contents to a route parameter with the same name, but gives the
visitor room to write.

## Syntax

```python
TextArea(name)
TextArea(name, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. Must be a valid Python parameter name. |
| `default_value` | `str` | `""` | The text shown before the visitor types. |

Like every component, `TextArea` also accepts
[styling and attribute keywords](../../keyword-attributes.md); `rows`
and `cols` control its size, and `placeholder` shows a hint.

## Examples

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    entry: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Journal"),
        "Latest entry:\n",
        state.entry + "\n",
        "Write today's entry:",
        TextArea("new_entry", "", rows=4),
        "\n",
        Button("Save entry", "save")
    ])


@route
def save(state: State, new_entry: str) -> Page:
    state.entry = new_entry
    return index(state)


start_server(State("Day 1: Domino the cat refused to be observed."))
```

## Notes

- The visitor's line breaks arrive in the parameter as `"\n"`
  characters in the string. Showing them again as separate lines needs
  [PreformattedText](../text/pre.md) or splitting the string yourself;
  a plain string on a page runs its lines together.
- The parameter should be annotated `str`; a text area is for prose,
  not numbers.

## Accessibility

Give every text area a visible label, and prefer `rows` generous
enough that writing is comfortable.

## Related components

- [TextBox](textbox.md): single-line input.
- [PreformattedText](../text/pre.md): showing multi-line text back
  with its line breaks intact.

## External links

- [The textarea element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/textarea)
