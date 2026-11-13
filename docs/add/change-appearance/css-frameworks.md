---
page_type: how-to
title: Use a CSS framework
level: L3
audience: S
priority: P2
prereqs: [add/change-appearance/custom-css]
symbols: []
outcome: Style a site with Bootstrap or Tailwind classes.
---

# Use a CSS framework

## Goal

You know Bootstrap or Tailwind, or you want their ready-made look,
and you want to use their class names on a Drafter site.

## Before you start

A CSS framework is a large stylesheet somebody else wrote. You do
not write rules; you put the framework's class names on your
components with the [`classes` keyword](../../reference/keyword-attributes.md),
and its rules do the rest.

## Two things to set up first

- **Turn off Drafter's theme.** A theme and a framework both try to
  style buttons, headings, and tables, and the result is a mix of
  the two. `set_website_style("none")` removes the theme so the
  framework is the only stylesheet in charge.
- **Expect to need the internet.** The lines below load the
  framework from a public server each time the page opens. Without
  a connection the page still works, but it is unstyled and shows a
  notice saying the styling did not load.

## Bootstrap

Bootstrap is one stylesheet. Link it with `add_website_css_file`, then
use its class names. `display-4`, `text-primary`, `alert`, and `btn`
are all Bootstrap class names, and its documentation lists the rest:

```python
# bootstrap_site.py
from drafter import *

set_website_style("none")
add_website_css_file(
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
)


@route
def index() -> Page:
    return Page([
        Header("Corgi Cafe", classes="display-4 text-primary"),
        Div("Ada recommends the peanut butter biscuits.",
            classes="alert alert-success"),
        Button("See the menu", "index", classes="btn btn-primary")
    ])


start_server()
```

## Tailwind

Tailwind works differently: a script reads the class names on your
page and writes the matching rules as it goes. Tailwind describes this
script as a tool for trying things out, and recommends a build step
for finished sites. For a class project it is fine; for a site with
real visitors, Bootstrap's plain stylesheet is the sturdier choice.
Load the script with `add_website_js_file`, using the version 4
address shown here:

```python
# tailwind_site.py
from drafter import *

set_website_style("none")
add_website_js_file(
    "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.1.11"
)


@route
def index() -> Page:
    return Page([
        Header("Corgi Cafe", classes="text-3xl font-bold text-blue-600 p-4"),
        Div("Ada recommends the peanut butter biscuits.",
            classes="m-4 rounded bg-emerald-100 p-4"),
        Button("See the menu", "index",
               classes="m-4 rounded bg-blue-600 px-4 py-2 text-white")
    ])


start_server()
```

## Common problems

- **The page is half styled, or buttons have the wrong colors**: a
  Drafter theme is still active. Add `set_website_style("none")`.
- **A notice says "Some of this page's styling did not load"**: the
  browser could not reach the framework's server. Check the
  connection and the spelling of the address, then reload.
- **Tailwind styles appear only after the first click**: the site is
  loading the older `cdn.tailwindcss.com` script, which leaves the
  first page unstyled until the visitor clicks something. Switch to
  the version 4 address above.
- **A class does nothing**: check its spelling against the
  framework's documentation, and check that it is inside the
  `classes="..."` string with spaces between names.
- **Bootstrap menus or pop-ups do not open**: those parts of
  Bootstrap also need its JavaScript file. This page covers styling
  only.

## Understand it

Frameworks are ordinary CSS reached through class names. See
[Custom CSS](custom-css.md) for how classes and selectors work, and
[Design basics](design-basics.md) for the spacing and color ideas
the class names stand for.

## See another example

[Use a theme](themes.md) gets a whole-site look in one line with no
class names at all, and is the simpler choice when a built-in theme
is close enough.

## Look it up

[Keyword attributes](../../reference/keyword-attributes.md) covers
`classes`. [Site configuration](../../reference/site-config.md)
covers `add_website_css_file`, `add_website_js_file`, and
`set_website_style`.

## Fix a problem

[Styling gotchas](gotchas.md) lists the surprises that come with
styling a Drafter page, and
[Troubleshooting](../../help/troubleshooting.md#the-page-looks-plain-or-unstyled)
covers a page that looks plain.
