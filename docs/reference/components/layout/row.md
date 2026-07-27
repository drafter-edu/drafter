---
page_type: component
title: Row
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Row
outcome: Lay content out side by side.
---

# Row

Group: [Layout](../index.md#layout)

## Description

A `Row` is a [Div](div.md) that arranges its contents side by side
instead of stacked, with everything vertically centered. It is the
simple answer to "these belong on one line": a label with its box,
buttons in a strip, columns in a card.

## Syntax

```python
Row(content, more_content, ...)
```

## Parameters

`Row` takes any number of strings and components as positional
arguments, laid out left to right. Like every component, it accepts
[styling and attribute keywords](../../keyword-attributes.md).

## Examples

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Mission Control"),
        Row("Callsign:", TextBox("callsign", "Rubber Duck 1")),
        Row(
            Button("Launch", "index"),
            Button("Abort", "index"),
            Button("Snacks", "index")
        ),
        Row(
            Div("LEFT PANEL", style_padding="10px",
                style_background_color="lavender"),
            Div("RIGHT PANEL", style_padding="10px",
                style_background_color="honeydew")
        )
    ])


start_server()
```

## Notes

- Under the hood a `Row` is a `div` with flexbox
  (`display: flex; flex-direction: row; align-items: center`), so
  every flexbox trick applies via `style_` keywords:
  `style_gap="12px"` spaces children, and
  `style_justify_content="space-between"` pushes them apart.
- Rows do not wrap by default; too many wide children overflow.
  `style_flex_wrap="wrap"` allows wrapping.
- In tests, a `Row` compares equal to a plain `Div` with the same
  contents and settings, so refactoring between them does not break
  structural assertions.

## Related components

- [Div (Box)](div.md): the stacked default.
- [Table](../data/table.md): when the side-by-side things are
  actually rows and columns of data.

## External links

- [Flexbox on MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout/Basic_concepts_of_flexbox)
