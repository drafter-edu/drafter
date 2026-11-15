---
page_type: reference
title: Keywords every component accepts
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Understand the extra keyword attributes components accept.
---

# Keywords every component accepts

Beyond its own parameters, every component accepts extra keyword
arguments. They fall into six families. Five of them work on any
component, from `Button` to `Table`. The sixth, `arguments`, has an
effect only on a component that calls a route.

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
attaches to an input. Use each id only once per page; when two
components share an id, targeting becomes unreliable.

## `on_*`: events that call routes

Keywords like `on_click`, `on_input`, and `on_change` name a route
(as a string, or the function itself) to run when that event
happens. The supported events are `blur`, `change`, `focus`, `input`,
`keydown`, `keyup`, `keypress`, `mouseenter`, `mouseleave`,
`mouseover`, `mouseout`, `click`, and `dblclick`. The concept, with
a worked demo, is [Live updates](../concepts/live-updates.md).

## `arguments`: extra values for the route

The `arguments` keyword sends fixed values to the route along with
whatever the visitor entered. It works on a `Button` or `Link`, and on
any component that has an `on_*` handler. The value can be a
dictionary of parameter names and values:

```python
TextBox("amount", "1", on_change="update", arguments={"row": 3})
```

When the visitor changes this box, Drafter calls `update` with the
box's value as `amount` and with `row` set to `3`.
[Passing arguments](components/actions/button.md#passing-arguments)
lists the other forms that `arguments` accepts.

## Plain HTML attributes

Each component also understands the HTML attributes that make sense
for its element: `placeholder="Type here"` or `maxlength=20` on a
`TextBox`, `rows=6` on a `TextArea`, `accept="image/*"` on a
`FileUpload`, `disabled=True` on a `Button`. The reference page for
each input component lists the attributes it recognizes. A shared
baseline of attributes (`id`, `title`, `hidden`, `data_*` attributes,
and similar) works on every component. Underscores become hyphens on
the way out, so `data_role="hero"` renders as `data-role="hero"`.

If a component does not recognize a keyword as an attribute, Drafter
treats the keyword as a CSS style instead. This rule is what makes
bare `color="red"` work, but it also means an unsupported attribute
quietly becomes a meaningless style rather than an error.

Some attributes act on the field itself: `maxlength` limits typing,
and `disabled=True` and `readonly=True` block editing. A disabled
field's value is not sent to the route. Attributes that ask the
browser to check a form do not stop a route from running. Drafter
does not ask the browser to check the form when a `Button` is
clicked, so a field marked `required=True` can be left empty, and a
value that breaks a `pattern`, a `minlength`, or a `min` and `max`
range still reaches the route. Check the values inside the route.

## Notes

- **Misspellings fail silently.** A misspelled `style_colour` or
  `on_clik` is not an error: it becomes a CSS property that no
  browser recognizes, so it has no visible effect. When a keyword
  seems to be ignored, check its spelling first.
- **Boolean attributes render bare**: `disabled=True` renders as
  `disabled`, the way HTML expects, and `disabled=False` omits the
  attribute entirely.
- **`autocomplete` keeps its value**: `autocomplete="off"` and
  `autocomplete="email"` render as written, and `True` and `False`
  render as `on` and `off`.
- **Styles set here are testable** with
  [assert_style](testing-functions.md#assert_style); other
  assertions ignore styling by default.

## Related

- [Styling functions](styling-functions.md): the same styles as
  wrapper functions.
- [Custom CSS](../add/change-appearance/custom-css.md): how to write
  CSS rules that use your `classes`.
- [Live updates](../concepts/live-updates.md): how to handle `on_*`
  events with routes.
