---
page_type: component
title: SVG
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - SVG
outcome: Show inline vector graphics.
---

# SVG

Group: [Media](../index.md#media)

## Description

An `SVG` draws vector graphics: shapes described by text, crisp
at any size. You write the shapes in SVG's own markup language
(circles, rectangles, lines, paths) and hand them to the
component as a string. Good for badges, diagrams, game boards,
and any graphic you want to generate from Python by building the
string.

## Syntax

```python
SVG(content, width=100, height=100)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `content` | `str` | required | The SVG markup for the shapes, rendered as written. |
| `width` | `int` | none | Display width in pixels. |
| `height` | `int` | none | Display height in pixels. |
| `viewBox` | `str` | none | The drawing's own coordinate system, like `"0 0 100 100"`; shapes use these coordinates regardless of display size. |

## Examples

Python builds the markup, so graphics can come from state:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    slices_eaten: int


@route
def index(state: State) -> Page:
    pizza = '<circle cx="50" cy="50" r="45" fill="gold" />'
    for slice_number in range(state.slices_eaten):
        angle = slice_number * 45
        pizza = pizza + (
            '<line x1="50" y1="50" x2="95" y2="50" stroke="white" '
            'stroke-width="8" transform="rotate(' + str(angle)
            + ' 50 50)" />'
        )
    return Page(state, [
        Header("Pizza Tracker"),
        SVG(pizza, width=150, height=150, viewBox="0 0 100 100"),
        "\n",
        Button("Eat a slice", "eat")
    ])


@route
def eat(state: State) -> Page:
    state.slices_eaten = min(8, state.slices_eaten + 1)
    return index(state)


start_server(State(0))
```

## Notes

- The content string is rendered as real markup, not escaped
  text, which makes this a cousin of
  [RawHTML](rawhtml.md): never build it from text a visitor
  typed.
- `viewBox` is what makes coordinates predictable: with
  `"0 0 100 100"`, your shapes live on a 100-by-100 grid no
  matter the display size.
- SVG's shape vocabulary (`circle`, `rect`, `line`, `path`,
  `text`) is its own language, worth ten minutes with the MDN
  tutorial below.
- For graphics a program draws and redraws imperatively,
  [Canvas](canvas.md) with JavaScript is the alternative; SVG
  wins when the picture is naturally a description.

## Related components

- [Canvas](canvas.md): a drawing surface for JavaScript.
- [Image](image.md): pictures from files rather than shapes.

## External links

- [SVG tutorial on MDN](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch)
