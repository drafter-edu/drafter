---
page_type: component
title: HorizontalRule
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - HorizontalRule
outcome: Add a divider line.
---

# HorizontalRule

Group: [Layout](../index.md#layout) · Level: L2

## Description

A `HorizontalRule` draws a line across the page: a visible divider
between one part of a page and the next. Use it where a page changes
topic, such as between displayed results and the form that changes
them.

## Syntax

```python
HorizontalRule()
```

## Parameters

`HorizontalRule` takes no positional parameters. Like every component,
it accepts [styling and attribute keywords](../../keyword-attributes.md).

## Examples

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    signed_in: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Guest Book"),
        "Guests so far: " + str(state.signed_in) + "\n",
        HorizontalRule(),
        "Add yourself:",
        TextBox("guest_name"),
        "\n",
        Button("Sign", "sign")
    ])


@route
def sign(state: State, guest_name: str) -> Page:
    state.signed_in = state.signed_in + 1
    return index(state)


start_server(State(0))
```

## Notes

- The rule sits on its own line automatically; no breaks needed
  around it.
- Its color and thickness come from the [theme](../../themes.md);
  restyle one with `style_` keywords if needed
  (`HorizontalRule(style_border="1px dashed gray")`).
- A rule is decoration with a hint of meaning ("new topic"). For real
  sectioning with titles, use [Header](../text/header.md).

## Related components

- [LineBreak](linebreak.md): a new line without a visible divider.
- [Header](../text/header.md): titled sections.

## External links

- [The hr element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/hr)
