---
page_type: playground
title: Styling
level: L2
audience: S
priority: P1
prereqs: []
symbols: []
outcome: See styling approaches side by side.
---

# Styling

This page shows the three tiers of styling (themes, helpers and
keywords, and real CSS), each in a demo you can experiment with. The
full story starts at
[Change the appearance](../../add/change-appearance/index.md).

## Tier 1: a theme changes everything

A single line restyles the whole site. Try swapping `"brutal"` for
`"latex"`, `"98"`, or anything else in the
[theme catalog](../../reference/themes.md).

```python drafter height=300
from drafter import *

set_website_style("brutal")


@route
def index() -> Page:
    return Page([
        Header("Themed in one line"),
        "Every component dresses to match.\n",
        TextBox("sample", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## Tier 2a: helpers wrap one thing

Each helper styles only the content it wraps. Helpers can also wrap
each other, so try nesting them.

```python drafter height=240
from drafter import *


@route
def index() -> Page:
    return Page([
        bold("Bold.\n"),
        italic("Italic.\n"),
        bold(italic(underline("All three at once.\n"))),
        change_color("Crimson.\n", "crimson"),
        change_background_color(
            change_padding("Padded on lavender.\n", "12px"), "lavender"),
        large_font(change_text_font("Fancy and large.\n", "Georgia"))
    ])


start_server()
```

The full list is in
[Styling functions](../../reference/styling-functions.md).

## Tier 2b: style keywords on any component

Every component accepts `style_*` keywords. The underscores in a
keyword become hyphens in the CSS property name, so
`style_background_color` sets `background-color`.

```python drafter height=240
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Dashboard", style_color="darkslateblue"),
        Button("Big friendly button", "index",
               style_font_size="24px",
               style_padding="12px",
               style_border_radius="12px"),
        "\n",
        Button("Suspicious button", "index",
               style_background_color="crimson",
               style_color="white")
    ])


start_server()
```

The full list of keywords is in
[Keywords every component accepts](../../reference/keyword-attributes.md).

## Tier 3: classes and real CSS

Define a rule once with `add_website_css`, then apply it anywhere
with `classes`. Change the rule, and every card updates to match.

```python drafter height=300
from drafter import *

add_website_css(".card", """
    border: 2px solid darkslateblue;
    border-radius: 8px;
    padding: 12px;
    margin: 8px;
    background-color: ghostwhite;
""")


@route
def index() -> Page:
    return Page([
        Header("Cards"),
        Div("The first card.", classes="card"),
        Div("The second card, same rule.", classes="card"),
        Div(bold("A card with helpers inside."), classes="card")
    ])


start_server()
```

The full story is in
[Custom CSS](../../add/change-appearance/custom-css.md).

## The box model, visualized

Margin is the space outside the border, and padding is the space
inside it. Change the three numbers and watch how the boxes shift.

```python drafter height=320
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Box Model"),
        Div(
            "margin 20px, border 4px, padding 24px",
            style_margin="20px",
            style_border="4px solid darkorange",
            style_padding="24px",
            style_background_color="cornsilk"
        ),
        Div(
            "no margin, thin border, no padding",
            style_border="1px solid gray"
        )
    ])


start_server()
```

For a friendlier explanation with diagrams, see
[Design basics](../../add/change-appearance/design-basics.md).

## Rows: side by side instead of stacked

`Row` lays its contents out horizontally. Try putting more things in
the row, or nesting a `Row` inside another `Row`.

```python drafter height=240
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Layout"),
        Row(
            Div("left", style_padding="8px",
                style_background_color="mistyrose"),
            Div("middle", style_padding="8px",
                style_background_color="honeydew"),
            Div("right", style_padding="8px",
                style_background_color="aliceblue")
        ),
        "\nA label and its box, on one line:",
        Row("Name:", TextBox("name"))
    ])


start_server()
```

## Where next

- [Change the appearance](../../add/change-appearance/index.md)
  helps you choose a tier deliberately.
- [Styling gotchas](../../add/change-appearance/gotchas.md) explains
  the surprising parts before you run into them.
