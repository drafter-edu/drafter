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
instead of stacked, with everything vertically centered. Use it when
several pieces of content belong on one line, such as a label next
to its text box, a strip of buttons, or the columns of a card.

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

- Internally, a `Row` is a `div` that uses flexbox
  (`display: flex; flex-direction: row; align-items: center`), so
  any flexbox technique can be applied through `style_` keywords:
  `style_gap="12px"` adds space between the children, and
  `style_justify_content="space-between"` spreads them apart.
- Rows do not wrap by default, so children that are too wide will
  overflow the row. Setting `style_flex_wrap="wrap"` allows the
  contents to wrap onto additional lines.
- In tests, a `Row` compares equal to a plain `Div` with the same
  contents and settings, so refactoring between them does not break
  structural assertions.

## Related components

- [Div (Box)](div.md): the same kind of container, without the
  side-by-side layout.
- [Table](../data/table.md): a better fit when the side-by-side
  content is really rows and columns of data.

## External links

- [Flexbox on MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout/Basic_concepts_of_flexbox)
