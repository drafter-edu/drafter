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
as a string parameter with the field's name. The string is a hex
code such as `"#ff8800"`, which works anywhere Drafter accepts a
color. Use it when the visitor should be free to pick any color;
when only a few colors are allowed, a [SelectBox](selectbox.md) of
color names is simpler.

## Syntax

```python
ColorPicker(name)
ColorPicker(name, default_value)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `default_value` | `str` | `"#000000"` (black) | The color the picker starts on, written as a hash sign and six hex digits, like `"#3366ff"`. |

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


start_server(State("#3366ff"))
```

## Notes

- The value is always a seven-character string: a hash sign and six
  hex digits, in lowercase. Annotate the receiving parameter as
  `str`.
- The starting color must use that same form. Color names such as
  `"red"` and short codes such as `"#f80"` raise an error when the
  picker is created, because a browser would otherwise replace them
  with black without saying so. The
  [color reference](../../colors.md) lists hex codes for the named
  colors.
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
