---
page_type: how-to
title: Custom CSS
level: L3
audience: S
priority: P1
prereqs: [add/change-appearance/design-basics]
symbols: []
outcome: Use real CSS with classes.
---

# Custom CSS

## Goal

The theme is close but not quite, and styling components one at a
time is getting repetitive. You want to write a rule once and have
it apply everywhere.

## Before you start

You have used [styling helpers](helpers.md) and know the
[box model](design-basics.md). CSS adds one idea to what you
already do: a *selector* says which elements a rule applies to, so
styling stops being per-component.

## The smallest version

`add_website_css` takes a selector and a rule body; `classes` tags
components so selectors can find them:

```python drafter height=300
from drafter import *

add_website_css(".notice", """
    border: 2px solid darkslateblue;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    background-color: ghostwhite;
""")


@route
def index() -> Page:
    return Page([
        Header("Announcements"),
        Div("The bake sale moved to Saturday.", classes="notice"),
        Div("Captain the cat has opinions about this.", classes="notice"),
        "Plain text stays plain."
    ])


start_server()
```

Change the rule once and every `notice` follows. That is the whole
trade: a little setup, then consistency for free.

## Selectors 101

The four you need, in order of usefulness:

| Selector | Applies to | Example |
| -------- | ---------- | ------- |
| `.name` | Components tagged `classes="name"` | `.notice` |
| `tag` | Every element of that HTML kind | `h1`, `button`, `a` |
| `.a .b` | Things tagged `b` inside things tagged `a` | `.card .title` |
| `#name` | The one component with `id="name"` | `#scoreboard` |

Tag selectors plus the component reference's "External links" tell
you what to target: a `Header(...)` at level 1 is an `h1`, every
`Button` is a `button`.

```python drafter height=260
from drafter import *

add_website_css("h1", "color: darkslateblue; letter-spacing: 2px;")
add_website_css("button", "border-radius: 999px; padding: 8px 16px;")


@route
def index() -> Page:
    return Page([
        Header("Rounded World"),
        Button("Every button", "index"),
        Button("Gets the treatment", "index")
    ])


start_server()
```

## Both forms of add_website_css

```python
add_website_css(".notice", "border: 2px solid navy;")
add_website_css(".notice { border: 2px solid navy; }")
```

With two arguments, the first is the selector and the second the
declarations to wrap in braces. With one argument, you are handing
over raw CSS, several rules at once if you like.

## Style tags inside a page

CSS from `add_website_css` applies sitewide. For a rule only one
page needs, the `Page`'s `css` parameter injects it with that page
only; it is an advanced corner documented on
[Page](../../reference/page.md).

## Where this sits with themes

Themes are CSS too, loaded before yours, so your rules usually win
when they target the same thing precisely. A theme with strong
opinions can still surprise you; when your rule seems ignored, see
the [specificity gotcha](gotchas.md). Building a look entirely your
own is easiest from `set_website_style("none")`, the blank slate.

## Common problems

- **The rule does nothing**: check the selector against the
  rendered reality: `classes="notice"` pairs with `.notice` (dot in
  the selector, not in the keyword), and misspelled selectors fail
  silently.
- **The rule styles too much**: `button` styles every button,
  including ones you forgot; prefer classes for anything less than
  a sitewide decision.
- **The theme fights back**: see
  [Styling gotchas](gotchas.md) for specificity and the escape
  hatches.
- **It styles the debug panel too**: broad selectors like `body`
  reach Drafter's own furniture; target your content instead (the
  [gotchas page](gotchas.md) names the right container).

## Understand it

[Design basics](design-basics.md) is the why behind the rules;
selectors are the only new machinery here.

## See another example

The [styling playground](../../examples/playground/styling.md) has
the three tiers side by side, cards included.

## Look it up

[add_website_css](../../reference/site-config.md#add_website_css)
and [classes](../../reference/keyword-attributes.md).

## Fix a problem

[Styling gotchas](gotchas.md): the weird parts, collected.
