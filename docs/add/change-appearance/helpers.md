---
page_type: how-to
title: Styling functions and keywords
level: L2
audience: S
priority: P0
prereqs: [add/change-appearance/design-basics]
symbols: []
outcome: Style individual components without CSS.
---

# Styling functions and keywords

## Goal

You want one particular thing on the page to be bold, or red, or
bigger, or spaced out, and you want the rest of the site left alone.

## Before you start

[Design basics](design-basics.md) introduced the box and the
properties that describe it. This page sets those properties from
Python, on one component at a time.

## A styling function wraps content

A styling function takes a piece of content and hands it back styled,
so the result goes wherever the content went. Wrap the result in a
second function to combine two effects:

```python drafter hl_lines="7-10" height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        bold("This line is bold.\n"),
        italic("This one is italic.\n"),
        change_color("This one is crimson.\n", "crimson"),
        bold(change_color("This one is both.\n", "crimson"))
    ])


start_server()
```

## Functions work on any component

Styling functions accept any component, not only text. Here a `Div`
holding a notice gets a border and padding, two of the layers from
Design basics, and a button gets bigger text:

```python drafter hl_lines="10-11 14" height=240
from drafter import *


@route
def index() -> Page:
    notice = Div(
        bold("Field trip on Friday!\n"),
        "Bring a raincoat and a snack."
    )
    notice = change_border(notice, "2px solid steelblue")
    notice = change_padding(notice, "12px")
    return Page([
        notice,
        large_font(Button("Sounds fun!", "index"))
    ])


start_server()
```

## One function for each property

Each of the seven properties from Design basics has a styling
function. It also has a style keyword, which the next section
explains:

| CSS property | Styling function | Style keyword |
| ------------ | ---------------- | ------------- |
| `color` | `change_color(content, "crimson")` | `style_color="crimson"` |
| `background-color` | `change_background_color(content, "lavender")` | `style_background_color="lavender"` |
| `border` | `change_border(content, "2px solid steelblue")` | `style_border="2px solid steelblue"` |
| `padding` | `change_padding(content, "12px")` | `style_padding="12px"` |
| `margin` | `change_margin(content, "8px")` | `style_margin="8px"` |
| `font-family` | `change_text_font(content, "Georgia")` | `style_font_family="Georgia"` |
| `font-size` | `change_text_size(content, "20px")` | `style_font_size="20px"` |

## Style keywords say the same thing inside the component

Every component also accepts `style_` keywords, one per CSS property,
right where the component is made:

```python drafter hl_lines="7 9-11" height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        Text("Big red button protocol.\n", style_font_size="20px"),
        Button("Do not press", "index",
               style_background_color="crimson",
               style_color="white",
               style_padding="10px")
    ])


start_server()
```

## The naming rule

A style keyword is `style_` followed by the CSS property name, with an
underscore wherever the property has a hyphen. The rule works for
every CSS property, including the ones with no styling function:

| CSS property | Style keyword |
| ------------ | ------------- |
| `color` | `style_color` |
| `background-color` | `style_background_color` |
| `font-size` | `style_font_size` |
| `border-radius` | `style_border_radius` |

Keyword arguments suit styling well because every `style_` setting is
optional, so you name only the ones you want.

## Functions or keywords?

Both do the same job. Functions read well when you make one or two
changes, and keywords keep everything in one place when a component
needs several. Here is the same line written both ways:

```python drafter hl_lines="7-8" height=180
from drafter import *


@route
def index() -> Page:
    return Page([
        bold(change_color("Lives: 3\n", "crimson")),
        Text("Lives: 3\n", style_color="crimson", style_font_weight="bold")
    ])


start_server()
```

## Common problems

- **The style did not apply**: check you are showing the wrapped result.
  `bold("hi")` returns styled content; it does not change `"hi"` in
  place.
- **A color or size seems ignored**: the value may be invalid CSS. Use a
  [named color](../../reference/colors.md) and include units on sizes
  (`"20px"`, not `20`).
- **A keyword seems misspelled**: remember the underscore rule.
  `style_background_color`, not `style_backgroundcolor`.
- **The theme overrides your style**: themes apply many rules of their
  own. Your inline styles usually win, but when one does not, try
  making the same change with a `style_` keyword, or pick a quieter
  theme.

## In more depth

### Every styling function, by what you want

The seven in the table above are the ones that match the box and its
properties. There are more:

| You want | Reach for |
| -------- | --------- |
| Emphasis | `bold`, `italic`, `underline`, `strikethrough`, `monospace` |
| Size | `small_font`, `large_font`, `change_text_size` |
| Color | `change_color`, `change_background_color` |
| Alignment | `change_text_align`, `float_left`, `float_right` |
| Spacing and boxes | `change_margin`, `change_padding`, `change_border`, `change_width`, `change_height` |
| Fonts and text shape | `change_text_font`, `change_text_decoration`, `change_text_transform` |

Color names come from the standard
[HTML color list](../../reference/colors.md), and safe font names from
the [font list](../../reference/fonts.md). For a property with no
function of its own, `update_style` sets any CSS property by name; see
[Styling functions](../../reference/styling-functions.md).

### A theme first, then the details

Styling functions and keywords work best on top of a
[theme](themes.md). The theme sets the overall look, and you style
only the details you want to stand out:

```python drafter hl_lines="4 16" height=280
from drafter import *
from dataclasses import dataclass

set_website_style("simple")


@dataclass
class State:
    lives: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Danger Zone"),
        bold(change_color("Lives remaining: " + str(state.lives), "crimson")),
        "\n",
        Button("Lose a life", "lose_life")
    ])


@route
def lose_life(state: State) -> Page:
    if state.lives > 0:
        state.lives = state.lives - 1
    return index(state)


start_server(State(3))
```

The rule of thumb is to use **themes for the whole site and styling
functions for moments of emphasis**. If you find yourself styling
every single component by hand, step back and pick a different theme
instead.

## Understand it

Styling changes presentation only, and leaves state and routes
untouched. The three ways to style a site are described on
[Change the appearance](index.md).

## See another example

[Finish and test an app](../../tutorials/finishing.md) applies a theme
plus targeted helpers to a finished project.

## Look it up

[Styling functions](../../reference/styling-functions.md) lists every
helper with its exact signature and CSS effect.

## Fix a problem

Styles are invisible to most tests by design, so cosmetic changes do
not break them. See [Test a feature](../test-a-feature.md) for
`assert_style` when you *do* want to check one. For display oddities,
start at [Troubleshooting](../../help/troubleshooting.md).
