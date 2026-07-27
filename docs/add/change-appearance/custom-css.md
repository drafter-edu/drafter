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
you no longer have to style one component at a time.

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

Change the rule once, and every `notice` changes with it. That is
the trade CSS offers: a little setup in exchange for consistency.

## Selectors 101

You need only four kinds of selector, listed here in order of
usefulness:

| Selector | Applies to | Example |
| -------- | ---------- | ------- |
| `.name` | Components tagged `classes="name"` | `.notice` |
| `tag` | Every element of that HTML kind | `h1`, `button`, `a` |
| `.a .b` | Things tagged `b` inside things tagged `a` | `.card .title` |
| `#name` | The one component with `id="name"` | `#scoreboard` |

To find which tag a component renders as, check the "External
links" section of its reference page: a `Header(...)` at level 1 is
an `h1`, and every `Button` is a `button`.

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

With two arguments, the first is the selector and the second is the
declarations that belong inside the braces. With one argument, you
are handing over raw CSS, which can contain several rules at once.

## Style tags inside a page

CSS from `add_website_css` applies to the whole site. When only one
page needs a rule, the `Page`'s `css` parameter attaches the rule
to that page alone. This is an advanced feature documented on
[Page](../../reference/page.md).

## Where this sits with themes

Themes are CSS too, and they load before yours, so your rules
usually win when they target the same element precisely. A strongly
opinionated theme can still override you; when your rule seems to
be ignored, see the [specificity gotcha](gotchas.md). To build a
look entirely your own, start from `set_website_style("none")`, the
blank slate.

## Common problems

- **The rule does nothing**: check the selector against what is
  actually rendered. `classes="notice"` pairs with `.notice` (the
  dot belongs in the selector, not in the keyword), and a
  misspelled selector fails silently.
- **The rule styles too much**: `button` styles every button,
  including ones you forgot about. Prefer classes for anything less
  than a sitewide decision.
- **The theme overrides your rule**: see
  [Styling gotchas](gotchas.md) for specificity and the ways around
  it.
- **It styles the debug panel too**: broad selectors like `body`
  also reach Drafter's own interface. Target your content instead;
  the [gotchas page](gotchas.md) names the right container.

## Understand it

[Design basics](design-basics.md) explains the reasoning behind the
rules. Selectors are the only new machinery on this page.

## See another example

The [styling playground](../../examples/playground/styling.md) has
the three tiers side by side, cards included.

## Look it up

[add_website_css](../../reference/site-config.md#add_website_css)
and [classes](../../reference/keyword-attributes.md).

## Fix a problem

[Styling gotchas](gotchas.md) collects the surprising parts of
styling in one place.
