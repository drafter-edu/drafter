---
page_type: reference
title: Styling functions
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - update_style
  - update_attr
  - float_right
  - float_left
  - bold
  - italic
  - underline
  - strikethrough
  - monospace
  - small_font
  - large_font
  - change_color
  - change_background_color
  - change_text_size
  - change_text_font
  - change_text_align
  - change_text_decoration
  - change_text_transform
  - change_height
  - change_width
  - change_border
  - change_margin
  - change_padding
outcome: Look up every styling helper.
---

# Styling functions

Every styling helper works the same way: it takes content, changes one
visual property, and returns the content, so helpers can wrap each
other. All of them accept a component, a plain string (wrapped in text
for you), or a list (each element is styled).

```python drafter height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        bold("Bold.\n"),
        change_color(italic("Crimson italics.\n"), "crimson"),
        change_background_color(
            change_padding("Boxed in.\n", "8px"), "lavender"),
        Button("Reload", "index")
    ])


start_server()
```

The how-to, organized by what you want to change, is
[Styling functions and keywords](../add/change-appearance/helpers.md).
This page is the full list.

## Text emphasis

| Function | Effect (CSS) |
| -------- | ------------ |
| `bold(content)` | `font-weight: bold` |
| `italic(content)` | `font-style: italic` |
| `underline(content)` | `text-decoration: underline` |
| `strikethrough(content)` | `text-decoration: line-through` |
| `monospace(content)` | `font-family: monospace` |
| `small_font(content)` | `font-size: small` |
| `large_font(content)` | `font-size: large` |

## Text appearance

Each of these takes the content first, then one string argument.

| Function | Second argument | Effect (CSS) |
| -------- | --------------- | ------------ |
| `change_color(content, color)` | A [color name](colors.md) or CSS color | `color` |
| `change_background_color(content, color)` | A color | `background-color` |
| `change_text_size(content, size)` | A size such as `"20px"` or a number of pixels | `font-size` |
| `change_text_font(content, font)` | A [font name](fonts.md) | `font-family` |
| `change_text_align(content, align)` | `"left"`, `"center"`, `"right"`, or `"justify"` | `text-align` |
| `change_text_decoration(content, decoration)` | Any CSS text decoration, such as `"underline dotted"` | `text-decoration` |
| `change_text_transform(content, transform)` | `"uppercase"`, `"lowercase"`, or `"capitalize"` | `text-transform` |

## Size and box

Values are CSS lengths: include units, as in `"200px"` or `"2em"`.
The box properties follow the CSS box model, explained with pictures
in [Design basics](../add/change-appearance/design-basics.md).

| Function | Effect (CSS) |
| -------- | ------------ |
| `change_height(content, height)` | `height` |
| `change_width(content, width)` | `width` |
| `change_border(content, border)` | `border`, e.g. `"2px solid black"` |
| `change_margin(content, margin)` | `margin`: space outside the border |
| `change_padding(content, padding)` | `padding`: space inside the border |

## Position

| Function | Effect (CSS) |
| -------- | ------------ |
| `float_left(content)` | `float: left`: content flows around the right side |
| `float_right(content)` | `float: right`: content flows around the left side |

## The general-purpose primitives

Every helper above is a shortcut for `update_style`, which can set any
CSS property by name:

```python
update_style("Warning!", "letter-spacing", "4px")
update_style(Button("Go", "index"), "border-radius", "50%")
```

Its sibling `update_attr` sets an HTML attribute instead of a style:

```python
update_attr(TextBox("guess"), "placeholder", "Type a number")
```

Both return the component, so calls chain. Remember units in style
values; `"20"` is not a size, `"20px"` is.

## Notes

- Helpers change how content looks, never what it is. Styling a value
  does not change your state, and styled components still compare as
  their underlying content plus settings in tests. `assert_style` can
  check styles directly; see
  [Testing functions](testing-functions.md).
- The same effects are available as `style_*` keyword arguments on any
  component (`Button("Go", "index", style_color="red")`); see
  [Keywords every component accepts](keyword-attributes.md).
- For sitewide changes, prefer a [theme](themes.md) or
  [add_website_css](site-config.md#add_website_css) over styling every
  component individually.

## Related

- [Styling functions and keywords](../add/change-appearance/helpers.md):
  the how-to.
- [Custom CSS](../add/change-appearance/custom-css.md): when helpers
  are not enough.
- [HTML colors](colors.md) and [Fonts](fonts.md).
