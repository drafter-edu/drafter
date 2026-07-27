---
page_type: concept
title: Design basics
level: L2
audience: S
priority: P1
prereqs: [add/change-appearance/helpers]
symbols: []
outcome: Apply spacing, color, and typography deliberately.
---

# Design basics

## In one sentence

Good-looking pages come from a few teachable habits, generous
space, restrained color, clear text hierarchy, not from talent.

## The idea

Visual design has rules the way code does, and the beginner-sized
set fits on one page:

**Space is a tool, not waste.** Crowded pages feel broken even when
they work. Give elements room with margin (space outside a border)
and padding (space inside it), group related things close together,
and let unrelated things drift apart. When a page feels wrong and
you cannot say why, the answer is usually "not enough space."

**Color wants restraint.** One main color plus one accent goes a
long way; a page with six colors has none. Two hard rules ride
along: text must contrast strongly with its background (squint; if
the text fades, so will your users), and color can never be the
only carrier of meaning, because not everyone sees it; pair color
with words or symbols ("Error: ..." in red, not just red).

**Typography is hierarchy.** Sizes should mean something: one page
title, section headings below it, body text below that, in
[Header](../../reference/components/text/header.md) levels used in
order. Long lines tire eyes; if text spans the whole window,
constrain it (`change_width(..., "40em")` is a fine ceiling).

**The box model is how CSS thinks about space.** Every element is a
box: content, wrapped in padding, wrapped in a border, wrapped in
margin. The helpers map straight onto it: `change_padding`,
`change_border`, `change_margin`.

## See it

The same content twice: crowded, then spaced and ranked. The only
differences are space, one accent color, and heading levels:

```python drafter height=420
from drafter import *


def crowded() -> list:
    return [
        Header("Bake Sale", 3),
        Header("Cookies", 3),
        "Chocolate chunk, oatmeal, mystery. All good. Probably.\n",
        Header("When", 3),
        "Saturday.\n"
    ]


def designed() -> list:
    return [
        Header("Bake Sale"),
        change_padding(Div(
            Header("Cookies", 2),
            change_width(
                "Chocolate chunk, oatmeal, mystery. All good. Probably.\n",
                "30em")
        ), "12px"),
        change_padding(Div(
            Header("When", 2),
            change_color(bold("Saturday.\n"), "darkslateblue")
        ), "12px")
    ]


@route
def index() -> Page:
    return Page(
        [Header("Crowded", 4), HorizontalRule()] + crowded() +
        [HorizontalRule(), Header("Designed", 4), HorizontalRule()] +
        designed()
    )


start_server()
```

Cause and effect: the designed version ranks its headings (one
level 1, sections at 2), boxes each section with padding, caps the
line length, and spends its single accent color on the one fact
that matters most.

## What this means for your code

- Apply a [theme](themes.md) first; themes embody most of these
  rules already, and your job shrinks to not fighting them.
- Reach for space before decoration: a `change_margin` fixes more
  pages than a `change_color`.
- Keep a tiny palette: pick two colors from the
  [color table](../../reference/colors.md) and stay loyal.
- Use `Header` levels for structure, styling functions for
  emphasis; never a `Header` just to make text big.
- Check contrast and colorblind-safety once per project: gray on
  white and red-vs-green meanings are the classic failures, and
  color-only meaning locks some users out entirely.

## Where people get confused

- **"Making it pretty means adding things."** Usually it means
  removing: fewer colors, fewer font sizes, more space.
- **"Margin and padding are the same."** Margin pushes neighbors
  away; padding pushes your own border away from your content. A
  background color fills padding but not margin, which is how to
  tell them apart on screen.
- **"It looks fine on my screen."** Yours is one size. Narrow the
  window and watch what happens; capped line widths and flexible
  layouts (see [Row](../../reference/components/layout/row.md))
  survive the squeeze.

## Go deeper

- [MDN's box model introduction](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Box_model)
  and [web.dev's design basics](https://web.dev/learn/design/)
  continue where this page stops.
- [Custom CSS](custom-css.md): the same ideas with real CSS
  selectors.
- [Improve the design](../../your-project/improve-the-design.md):
  a usability pass for your project.
