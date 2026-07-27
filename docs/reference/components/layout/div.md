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

A `Div` is a box around content. It is invisible on its own, but it
is the standard component to style, space, and tag with
[classes](../../keyword-attributes.md). When several pieces of
content should be treated as one unit (a card, a section, a panel),
wrap them in a `Div`.

## Syntax

```python
Div(content, more_content, ...)
```

## Parameters

`Div` takes any number of strings and components as positional
arguments, which become its contents in order. Like every component,
it accepts
[styling and attribute keywords](../../keyword-attributes.md);
applying those is usually the reason to use a `Div` in the first
place.

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

Writing a helper function that returns a styled `Div`, as this
example does, keeps repeated visual units consistent.

## Notes

- A `Div` starts on its own line and stretches full width; for
  inline grouping use [Span](span.md), and for side-by-side layout
  use [Row](row.md).
- `Box` and `Division` are aliases for the same component.
- An unstyled `Div` does nothing visible; if you are wrapping
  content without adding styling or a class, you probably do not
  need the wrapper.

## Related components

- [Span](span.md): groups content inline instead of in a block.
- [Row](row.md): a `Div` that arranges its contents side by side.
- [Custom CSS](../../../add/change-appearance/custom-css.md):
  shows how classes and `Div`s combine into the card pattern.

## External links

- [The div element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/div)
