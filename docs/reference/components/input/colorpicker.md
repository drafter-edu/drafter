---
page_type: component
title: ColorPicker
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - ColorPicker
outcome: Collect a color.
---

# ColorPicker

Group: [Input](../index.md#input)

## Description

A `ColorPicker` shows a small swatch. Clicking it opens the
browser's color chooser, and the chosen color arrives at the route
as a parameter with the field's name. Use it when the visitor should
be free to pick any color; when only a few colors are allowed, a
[SelectBox](selectbox.md) of color names is simpler.

## Syntax

```python
ColorPicker(name)
ColorPicker(name, default_value)
ColorPicker(name, default_value, alpha=True)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `default_value` | `str`, `list`, `tuple`, or [`Color`](../../data-types/color.md) | black | The color the picker starts on. See the ways to write it below. |
| `alpha` | `bool` | `False` | Also let the visitor choose how see-through the color is. |

The starting color can be written any of these ways:

| Written as | Example |
| ---------- | ------- |
| A hex code | `"#ff8800"` |
| A short hex code, where each digit is doubled | `"#f80"` |
| A [color name](../../colors.md) | `"tomato"` |
| A list or tuple of red, green, and blue amounts from 0 to 255 | `[255, 136, 0]` |
| A `Color` | `Color(255, 136, 0)` |

## Examples

The chosen color is stored in state and used to style a piece of
text:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    collar: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Collar Shop"),
        Span("Babbage's new collar", style_color=state.collar,
             style_font_weight="bold"),
        "\nPick a color:",
        ColorPicker("collar", state.collar),
        "\n",
        Button("Try it on", "try_on")
    ])


@route
def try_on(state: State, collar: str) -> Page:
    state.collar = collar
    return index(state)


start_server(State("royalblue"))
```

The annotation on the route's parameter decides what form the color
arrives in. With `list[int]` you get the red, green, and blue
amounts as numbers you can calculate with:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    amounts: list[int]


@route
def index(state: State) -> Page:
    brightness = sum(state.amounts) // 3
    return Page(state, [
        Header("How bright is it?"),
        "Red, green, blue: " + str(state.amounts),
        "\nBrightness out of 255: " + str(brightness),
        "\n",
        ColorPicker("paint", state.amounts),
        "\n",
        Button("Measure", "measure")
    ])


@route
def measure(state: State, paint: list[int]) -> Page:
    state.amounts = paint
    return index(state)


start_server(State([255, 136, 0]))
```

With `alpha=True`, a slider appears beside the swatch for how
see-through the color is, and the color you receive carries that
amount too:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    paint: Color


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Window Paint"),
        Div("Domino is hiding behind this.",
            style_background_color=state.paint, style_padding="12px"),
        "\nOpacity out of 255: " + str(state.paint.alpha),
        "\n",
        ColorPicker("paint", state.paint, alpha=True),
        "\n",
        Button("Repaint", "repaint")
    ])


@route
def repaint(state: State, paint: Color) -> Page:
    state.paint = paint
    return index(state)


start_server(State(Color(51, 102, 255, 128)))
```

## What the route receives

| Parameter annotation | Value | With `alpha=True` |
| -------------------- | ----- | ----------------- |
| `str` | `"#ff8800"` | `"#ff880080"` |
| `list[int]` | `[255, 136, 0]` | `[255, 136, 0, 128]` |
| [`Color`](../../data-types/color.md) | `Color(255, 136, 0)` | `Color(255, 136, 0, 128)` |

Each amount is a whole number from 0 to 255. For `alpha`, 0 is
invisible and 255 is completely solid.

## Notes

- Hex codes arrive in lowercase. A color given by name or as a list
  is turned into its hex code when the picker is created, so
  `ColorPicker("ink", "red")` and `ColorPicker("ink", "#ff0000")`
  are equal in tests.
- A starting color Drafter cannot read raises an error when the
  picker is created, because a browser would otherwise replace it
  with black without saying so. A misspelled color name gets a
  suggestion, such as `'tomato'` for `'tomatoe'`.
- With `alpha=False`, an alpha amount in the starting color is
  dropped, so a `Color` saved from an earlier pick can always be
  passed back in.
- A color picker always submits a color; there is no "empty" choice.
- The browser controls what the chooser looks like, so it differs
  between computers and phones.

## Accessibility

The swatch alone does not say what the color is for. Put a short
description right before it (the "Pick a color:" text above, or a
[Label](label.md)). When the chosen color is used for text, check
that it stays readable against the background; a pale yellow on
white is hard for anyone to read.

## Related components

- [SelectBox](selectbox.md): offer a short list of named colors.
- [Slider](slider.md): collect a number from a range.

## External links

- [The color input on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/color)
- [Styling functions](../../styling-functions.md)
