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

Good-looking pages come from a few teachable habits (generous
space, restrained color, and clear text hierarchy) rather than from
talent.

## The idea

Visual design has rules the way code does, and the beginner-sized
set fits on one page:

**Space is a tool, not waste.** Crowded pages feel broken even when
they work. Give elements room with margin (space outside a border)
and padding (space inside it), group related things close together,
and let unrelated things drift apart. When a page feels wrong and
you cannot say why, the answer is usually "not enough space."

**Color needs restraint.** One main color plus one accent goes a
long way, while a page with six colors has no clear emphasis at
all. Two hard rules come with color. First, text must contrast
strongly with its background; squint at the page, and if the text
fades for you, it will fade for your users. Second, color can never
be the only carrier of meaning, because not everyone perceives
color; pair it with words or symbols, such as writing "Error: ..."
in red rather than relying on red alone.

**Typography is hierarchy.** Sizes should mean something: one page
title, section headings below it, and body text below that, with
[Header](../../reference/components/text/header.md) levels used in
order. Long lines tire the eyes, so if text spans the whole window,
constrain its width (`change_width(..., "40em")` is a reasonable
ceiling).

**The box model is how CSS thinks about space.** Every element is a
box: content, wrapped in padding, wrapped in a border, wrapped in
margin. The helpers map straight onto it: `change_padding`,
`change_border`, `change_margin`.

## See it

This demo shows the same content twice: first crowded, then spaced
and ranked. The only differences are space, one accent color, and
heading levels:

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

Compare cause and effect: the designed version ranks its headings
(one at level 1, sections at level 2), boxes each section with
padding, caps the line length, and spends its single accent color
on the one fact that matters most.

## What this means for your code

- Apply a [theme](themes.md) first; themes embody most of these
  rules already, so your main job becomes not fighting them.
- Reach for space before decoration: a `change_margin` fixes more
  pages than a `change_color`.
- Keep a tiny palette: pick two colors from the
  [color table](../../reference/colors.md) and use only those.
- Use `Header` levels for structure and styling functions for
  emphasis. Never use a `Header` only to make text bigger.
- Check contrast and colorblind-safety once per project: gray text
  on a white background and red-versus-green distinctions are the
  classic failures, and meaning carried only by color locks some
  users out entirely.

## Where people get confused

- **"Making it pretty means adding things."** Usually it means
  removing: fewer colors, fewer font sizes, more space.
- **"Margin and padding are the same."** Margin pushes neighbors
  away; padding pushes your own border away from your content. A
  background color fills padding but not margin, which is how to
  tell them apart on screen.
- **"It looks fine on my screen."** Your screen is only one of many
  sizes. Narrow the window and watch what happens: capped line
  widths and flexible layouts (see
  [Row](../../reference/components/layout/row.md)) hold up when the
  window shrinks.

## Go deeper

- [MDN's box model introduction](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Box_model)
  and [web.dev's design basics](https://web.dev/learn/design/)
  continue where this page stops.
- [Custom CSS](custom-css.md) applies the same ideas with real CSS
  selectors.
- [Improve the design](../../your-project/improve-the-design.md)
  walks through a usability pass for your project.
