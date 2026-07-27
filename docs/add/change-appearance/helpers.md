---
page_type: how-to
title: Styling functions and keywords
level: L2
audience: S
priority: P0
prereqs: [add/change-appearance]
symbols: []
outcome: Style individual components without CSS.
---

# Styling functions and keywords

## Goal

You want one particular thing on the page to be bold, or red, or bigger,
or spaced out, without touching the rest of the site.

## Before you start

A theme handles the overall look ([use one first](themes.md)). Helpers
are for the details: they wrap a single piece of content and return it
styled.

## The smallest version

Wrap content in a styling function. Wrap the wrapper to combine effects:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    warnings: int


@route
def index(state: State) -> Page:
    return Page(state, [
        bold("This line is bold.\n"),
        italic("This one is italic.\n"),
        change_color("This one is crimson.\n", "crimson"),
        bold(change_color("Warnings: " + str(state.warnings) + "\n", "darkorange")),
        Button("Add a warning", "warn")
    ])


@route
def warn(state: State) -> Page:
    state.warnings = state.warnings + 1
    return index(state)


start_server(State(0))
```

## The helpers, by what you want

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
the [font list](../../reference/fonts.md).

## Recipe: style components, not just text

Helpers accept any component. A button can be big and green; a whole
group can get a border by wrapping a `Div`:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    accepted: bool


@route
def index(state: State) -> Page:
    notice = Div(
        bold("Field trip on Friday!\n"),
        "Bring a raincoat and a snack.\n"
    )
    return Page(state, [
        change_padding(change_border(notice, "2px solid steelblue"), "12px"),
        "\n",
        large_font(change_background_color(Button("Sounds fun!", "accept"), "lightgreen"))
    ])


@route
def accept(state: State) -> Page:
    state.accepted = True
    return Page(state, [
        "See you Friday!"
    ])


start_server(State(False))
```

## Recipe: style keywords on any component

Every component also accepts `style_` keyword arguments directly, one
per CSS property. The part after `style_` is the CSS property name with
underscores instead of hyphens, so `style_background_color` sets
`background-color`:

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    presses: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Text("Big red button protocol.\n", style_font_size="20px"),
        Button("Do not press", "press",
               style_background_color="crimson",
               style_color="white",
               style_padding="10px")
    ])


@route
def press(state: State) -> Page:
    state.presses = state.presses + 1
    return Page(state, [
        "Pressed " + str(state.presses) + " times. Naturally.\n",
        Button("Back", "index")
    ])


start_server(State(0))
```

Helpers and keywords do the same job; helpers read better for one or two
changes, keywords keep everything in one place when a component needs
several. These are the moments where keyword arguments are the right
tool, because every `style_` setting is optional.

## Common problems

- **The style did not apply**: check you are showing the wrapped result.
  `bold("hi")` returns styled content; it does not change `"hi"` in
  place.
- **A color or size seems ignored**: the value may be invalid CSS. Use a
  [named color](../../reference/colors.md) and include units on sizes
  (`"20px"`, not `20`).
- **The theme overrides your style**: themes are strong. Your inline
  styles usually win, but if one does not, try the same change as a
  `style_` keyword, or a quieter theme.
- **A keyword seems misspelled**: remember the underscore rule.
  `style_background_color`, not `style_backgroundcolor`.

## Understand it

Styling changes presentation only; state and routes are untouched. The
three tiers are on [Change the appearance](index.md).

## See another example

[Finish and test an app](../../tutorials/finishing.md) applies a theme
plus targeted helpers to a finished project.

## Look it up

[Styling functions](../../reference/styling-functions.md): every helper
with its exact signature and CSS effect.

## Fix a problem

Styles are invisible to most tests by design (cosmetic changes should
not break them); see
[Test a feature](../test-a-feature.md) for `assert_style` when you *do*
want to check one. For display oddities, start at
[Troubleshooting](../../help/troubleshooting.md).
