---
page_type: reference
title: Keywords every component accepts
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - PageContent
  - Content
  - Component
outcome: Understand the extra keyword attributes components accept.
---

# Keywords every component accepts

Beyond its own parameters, every component accepts extra keyword
arguments. They fall into five families, and all five work on any
component, from `Button` to `Table`.

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Every family at once", style_color="darkslateblue"),
        Button("Styled", "index", style_font_size="20px"),
        "\n",
        TextBox("word", "", placeholder="an HTML attribute at work"),
        "\n",
        Button("Wired", "index", on_mouseenter="react"),
        "\n",
        Output("noticeboard", ["Hover the Wired button."])
    ])


@route
def react() -> Fragment:
    return Fragment(["I felt that."], target="#noticeboard")


start_server()
```

## `style_*`: one CSS property each

Any keyword starting with `style_` sets the matching CSS property on
that component. Underscores become hyphens:
`style_background_color="lavender"` sets `background-color`.
Values are CSS text, units included (`"20px"`, not `20`).

The [styling functions](styling-functions.md) set exactly the same
properties from outside the constructor; use whichever reads better.

## `classes`: names for CSS to find

`classes="card"` (or `classes="card highlighted"` for several) tags
the component so a CSS rule from
[add_website_css](site-config.md#add_website_css) or a
[theme](themes.md) can find it. The how-to is
[Custom CSS](../add/change-appearance/custom-css.md).

## `id`: a name for targeting

`id="scoreboard"` gives the component a unique name on the page.
Ids are how a [Fragment](fragment.md) finds its target
(`target="#scoreboard"`) and how a [Label](components/input/label.md)
attaches to an input. One id per page per name; duplicates confuse
targeting.

## `on_*`: events that call routes

Keywords like `on_click`, `on_input`, and `on_change` name a route
(as a string, or the function itself) to run when that event
happens. The supported events: `blur`, `change`, `focus`, `input`,
`keydown`, `keyup`, `keypress`, `mouseenter`, `mouseleave`,
`mouseover`, `mouseout`, `click`, and `dblclick`. The concept, with
a worked demo, is [Live updates](../concepts/live-updates.md).

## Plain HTML attributes

Each component also understands the HTML attributes that make sense
for its element: `placeholder="Type here"` or `maxlength=20` on a
`TextBox`, `rows=6` on a `TextArea`, `accept="image/*"` on a
`FileUpload`, `disabled=True` on a `Button`. A shared baseline
(`id`, `title`, `hidden`, `data_*` attributes, and friends) works
everywhere. Underscores become hyphens on the way out, so
`data_role="hero"` renders as `data-role="hero"`.

A keyword the component does not recognize as an attribute is
treated as a CSS style instead (that rule is what makes bare
`color="red"` work), so an unsupported attribute quietly becomes a
meaningless style rather than an error.

## Notes

- **Spelling matters silently.** A misspelled `style_colour` or
  `on_clik` is not an error; it lands as a CSS property no browser
  recognizes and does nothing visible. When a keyword seems ignored,
  check its spelling first.
- **Boolean attributes render bare**: `disabled=True` renders as
  `disabled`, the way HTML expects, and `disabled=False` omits the
  attribute entirely.
- **Styles set here are testable** with
  [assert_style](testing-functions.md#assert_style); other
  assertions ignore styling by default.

## Related

- [Styling functions](styling-functions.md): the same styles as
  wrapper functions.
- [Custom CSS](../add/change-appearance/custom-css.md): making
  `classes` do work.
- [Live updates](../concepts/live-updates.md): making `on_*` do
  work.
