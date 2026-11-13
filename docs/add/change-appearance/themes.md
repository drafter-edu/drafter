---
page_type: how-to
title: Use a theme
level: L2
audience: S
priority: P0
prereqs: [add/change-appearance]
symbols: []
outcome: Restyle the whole site in one line.
---

# Use a theme

## Goal

You want the whole site to look polished without styling anything by
hand.

## Before you start

You only need to know how to run an app. A theme is a complete,
ready-made look (colors, fonts, spacing, and button styles) applied to
every page at once.

## One line restyles the site

Applying a theme takes one line, placed after the imports and before
`start_server(...)`. Swap `"terminal"` for any of the names further
down this page, then run the program again:

```python drafter hl_lines="3" height=300
from drafter import *

set_website_style("terminal")


@route
def index() -> Page:
    return Page([
        Header("Coin Collector"),
        "Coins so far: 3\n",
        Button("Count again", "index"),
        Link("Start over", "index")
    ])


start_server()
```

## Twenty themes

Every theme has a short name. Most of them fall into a few kinds:

| Kind | Names |
| ---- | ----- |
| Drafter's own look, which you get without choosing | `default` |
| A blank slate for [custom CSS](custom-css.md) | `none` |
| Quiet | `simple`, `sakura`, `water` |
| Old operating systems | `98`, `xp`, `7` |
| Everything else | `almond`, `brutal`, `daub`, `latex`, `magick`, `mvp`, `pico`, `retro`, `skeleton`, `tacit`, `terminal`, `yorha` |

The [theme catalog](../../reference/themes.md) previews each one. You
can also try them without editing code: while your app is running
with the debug panel open, the panel's theme switcher previews themes
live. When you find one you like, write its name into
`set_website_style(...)` to make the choice permanent.

## Common problems

- **The theme did not apply**: `set_website_style(...)` must run before
  `start_server(...)`. Top of the file, right after imports.
- **A misspelled name**: the error lists every valid theme and suggests
  the closest match to what you typed.
- **You want no styling at all**: there is a theme for that as well,
  `set_website_style("none")`.
- **The theme clashes with your own styling**: strong themes style
  everything. Either accept the theme's choices, pick a quieter theme
  (`simple`, `sakura`, `water`), or switch to `none` and add
  [custom CSS](custom-css.md).

## In more depth

### Where each theme comes from

Most themes are stylesheets that other people wrote and shared. This
table lists every valid name, along with the stylesheet each theme is
based on:

| Name | Based on |
| ---- | -------- |
| `default` | Drafter's own look (what you get without choosing) |
| `none` | No styling at all: a blank slate for [custom CSS](custom-css.md) |
| `almond` | Almond.CSS by Alvaro Montoro |
| `brutal` | Brutal by Vitor Estevam |
| `daub` | Daub UI Kit by Sliday |
| `latex` | LaTeX.css by Vincent Doerig |
| `magick` | magick.css by winterveil |
| `mvp` | MVP.css by andybrewer |
| `pico` | Pico CSS |
| `retro` | retro (markdowncss) by John Otander |
| `sakura` | Sakura by oxal |
| `simple` | Simple.css by kevquirk |
| `skeleton` | Skeleton by Dave Gamache |
| `tacit` | Tacit by yegor256 |
| `terminal` | Terminal theme by panr |
| `water` | Water.css (dark) by Kognise |
| `yorha` | YoRHa CSS by Ethan Chan |
| `98` | 98.css by jdan (a 1998 operating system) |
| `xp` | XP.css by botoxparty (a 2001 operating system) |
| `7` | 7.css by khang-nd (a 2009 operating system) |

## Understand it

Themes are stylesheets applied over your content, and they never change
your state or routes. The three ways to style a site are described on
[Change the appearance](index.md).

## See another example

The [theme catalog](../../reference/themes.md) previews all twenty, and
[Finish and test an app](../../tutorials/finishing.md) picks one for a
real project.

## Look it up

[Site configuration](../../reference/site-config.md) for
`set_website_style` and its relatives.

## Fix a problem

A bad theme name produces a friendly error with suggestions. For
anything stranger, start at
[Troubleshooting](../../help/troubleshooting.md).
