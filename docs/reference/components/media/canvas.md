---
page_type: component
title: Canvas
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Canvas
outcome: Draw on a canvas surface (with JavaScript).
---

# Canvas

Group: [Media](../index.md#media)

## Description

A `Canvas` places a blank drawing surface on the page. The
component itself only reserves the space and gives it an id; the
drawing happens through the browser's canvas API, reached from
Python via Pyodide's `js` module or from JavaScript you add to
the page. That makes this the most advanced component in the
media group: nothing appears without interop code.

## Syntax

```python
Canvas(canvas_id)
Canvas(canvas_id, width=400, height=200)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `canvas_id` | `str` | required | The id your drawing code uses to find the surface. |
| `width` | `int` | `300` | Drawing surface width in pixels. |
| `height` | `int` | `150` | Drawing surface height in pixels. |

## Examples

The canvas is found by id and drawn on with the browser's own
drawing calls (this demo uses the `js` module, which only exists
in the browser):

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Doodle"),
        Canvas("doodle", width=300, height=120),
        "\n",
        Button("Draw a sunset", "draw")
    ])


@route
def draw(state: State) -> Page:
    import js
    canvas = js.document.getElementById("doodle")
    if canvas is not None:
        brush = canvas.getContext("2d")
        brush.fillStyle = "coral"
        brush.fillRect(0, 0, 300, 120)
        brush.fillStyle = "gold"
        brush.beginPath()
        brush.arc(150, 120, 40, 3.14, 0)
        brush.fill()
    return Update(state)


start_server(State())
```

## Notes

- The route returns `Update` rather than a new `Page`: a
  re-render would replace the canvas with a fresh blank one,
  erasing the drawing. Draw onto the live page, change nothing
  else.
- `import js` only works in the browser, which is where routes
  run; the same import at the top of the file would fail during
  the local run.
- Before committing to canvas interop, check whether
  [SVG](svg.md) can draw your picture from a string, or whether
  [MatPlotLibPlot](matplotlibplot.md) covers it; both stay in
  ordinary Python.
- Everything about the drawing API (paths, colors, images,
  text) is the browser's own; the MDN tutorial below is the
  manual.

## Related components

- [SVG](svg.md): graphics as markup, no interop needed.
- [Image](image.md): showing a picture that already exists.

## External links

- [Canvas tutorial on MDN](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)
- [Python in the browser](../../../extend/pyodide.md): what the
  `js` module is.
