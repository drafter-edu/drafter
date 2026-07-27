---
page_type: component
title: Div (Box)
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Div
  - Division
  - Box
outcome: Group content for styling.
---

# Div (Box)

Group: [Layout](../index.md#layout)

## Description

A `Div` is a box around content: invisible by itself, and the
standard thing to style, space, and tag with
[classes](../../keyword-attributes.md). When several pieces of
content should be treated as one unit (a card, a section, a panel),
wrap them in a `Div`.

## Syntax

```python
Div(content, more_content, ...)
```

## Parameters

`Div` takes any number of strings and components as positional
arguments, its contents in order. Like every component, it accepts
[styling and attribute keywords](../../keyword-attributes.md),
which is usually the point of using one.

## Examples

```python drafter height=280
from drafter import *


def pet_card(name: str, species: str) -> PageContent:
    return Div(
        Header(name, 3),
        species + "\n",
        Button("Adopt " + name, "index"),
        style_border="2px solid darkseagreen",
        style_border_radius="8px",
        style_padding="12px",
        style_margin="8px"
    )


@route
def index() -> Page:
    return Page([
        Header("Adoption Corner"),
        pet_card("Babbage", "A small black mutt of great enthusiasm."),
        pet_card("Domino", "A black cat of great dignity.")
    ])


start_server()
```

A helper returning a styled `Div`, as here, is how repeated visual
units stay consistent.

## Notes

- A `Div` starts on its own line and stretches full width; for
  inline grouping use [Span](span.md), and for side-by-side layout
  use [Row](row.md).
- `Box` and `Division` are aliases for the same component.
- Unstyled `Div`s do nothing visible; if you are wrapping without
  styling or classing, you probably do not need the wrapper.

## Related components

- [Span](span.md): the inline sibling.
- [Row](row.md): a Div that lays out horizontally.
- [Custom CSS](../../../add/change-appearance/custom-css.md):
  classes plus Divs, the card pattern.

## External links

- [The div element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/div)
