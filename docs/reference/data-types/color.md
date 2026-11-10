---
page_type: reference
title: Color
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - Color
outcome: Work with a color as red, green, blue, and alpha amounts.
---

# Color

A `Color` is a color broken into the amounts a screen mixes to show
it: how much red, how much green, how much blue, and how solid it
is. A [ColorPicker](../components/input/colorpicker.md) hands you
one when its route parameter is annotated with `Color`, and you can
build your own.

## Fields

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `red` | `int` | Amount of red, from 0 (none) to 255 (full). |
| `green` | `int` | Amount of green, from 0 to 255. |
| `blue` | `int` | Amount of blue, from 0 to 255. |
| `alpha` | `int` | How solid the color is, from 0 (invisible) to 255 (completely solid). Defaults to 255. |

All four use the same 0 to 255 scale. That is the scale a
[Picture](picture.md)'s pixels use too, so a `Color`'s amounts can
go straight into a pixel.

## Making one

```python
orange = Color(255, 136, 0)
faint_orange = Color(255, 136, 0, 64)

Color.from_hex("#ff8800")
Color.from_hex("#f80")       # short form: each digit is doubled
Color.from_name("tomato")    # any of the browser's color names
```

`Color.from_name` knows the same 148 names a browser does, listed
in the [color reference](../colors.md). Capital letters and spaces
do not matter, so `"Steel Blue"` and `"steelblue"` are the same
color. A misspelled name raises an error that suggests the closest
real ones.

## Using one

A `Color` can go anywhere Drafter takes a color. It turns itself
into a hex code when it is used that way:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    collar: Color


@route
def index(state: State) -> Page:
    darker = Color(state.collar.red // 2, state.collar.green // 2,
                   state.collar.blue // 2)
    return Page(state, [
        Span("Babbage's collar", style_color=state.collar,
             style_font_weight="bold"),
        "\n",
        Span("and its shadow", style_color=darker),
        "\nPick a color:",
        ColorPicker("collar", state.collar),
        "\n",
        Button("Try it on", "try_on")
    ])


@route
def try_on(state: State, collar: Color) -> Page:
    state.collar = collar
    return index(state)


start_server(State(Color(51, 102, 255)))
```

Because the amounts are plain numbers, you can do arithmetic on
them, as the "shadow" above does by halving each one.

## Methods

| Call | Gives |
| ---- | ----- |
| `color.to_hex()` | The hex code as text, like `"#ff8800"`. A color that is not fully solid gets two more digits for its alpha, like `"#ff880040"`. |
| `color.to_hex(alpha=True)` | Always eight digits. `alpha=False` always gives six. |
| `color.to_list()` | `[red, green, blue]`, with `alpha` as a fourth item when the color is not fully solid. Takes the same `alpha` option as `to_hex`. |
| `str(color)` | The same as `color.to_hex()`. |

## Notes

- Every amount must be a whole number from 0 to 255. Anything else
  raises an error naming the amount that is out of range.
- Two colors are equal when all four amounts match, so
  `Color(255, 0, 0) == Color.from_name("red")` is `True`.
- `"transparent"` is accepted as a name and gives a color with every
  amount at 0.

## Related

- [ColorPicker](../components/input/colorpicker.md): let a visitor
  choose a color.
- [Color names](../colors.md): the 148 named colors and their hex
  codes.
- [Styling functions](../styling-functions.md): where colors get
  used.
