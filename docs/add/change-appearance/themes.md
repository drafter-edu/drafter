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

Nothing to know beyond running an app. A theme is a complete, ready-made
look, colors, fonts, spacing, button styles, applied to every page at
once.

## The smallest version

One line, placed after the imports and before `start_server(...)`:

```python drafter height=300
from drafter import *
from dataclasses import dataclass

set_website_style("terminal")


@dataclass
class State:
    coins: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Coin Collector"),
        "Coins: " + str(state.coins) + "\n",
        Button("Grab a coin", "grab"),
        Button("Spend them all", "spend")
    ])


@route
def grab(state: State) -> Page:
    state.coins = state.coins + 1
    return index(state)


@route
def spend(state: State) -> Page:
    state.coins = 0
    return index(state)


start_server(State(0))
```

Edit the demo and swap `"terminal"` for any name below, then run it
again.

## The theme names

Every valid name, with the stylesheet each is based on:

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

See the [theme catalog](../../reference/themes.md) for previews of each
one.

## Trying themes quickly

While your app is running with the debug panel open, the panel's theme
switcher lets you preview themes live without editing code. When you
find one you like, write it into `set_website_style(...)` so it sticks.

## Common problems

- **The theme did not apply**: `set_website_style(...)` must run before
  `start_server(...)`. Top of the file, right after imports.
- **A misspelled name**: the error lists every valid theme and suggests
  the closest match to what you typed.
- **You want no styling at all**: that is a theme too:
  `set_website_style("none")`.
- **The theme clashes with your own styling**: strong themes style
  everything. Either accept the theme's choices, pick a quieter theme
  (`simple`, `sakura`, `water`), or go to `none` plus
  [custom CSS](custom-css.md).

## Understand it

Themes are stylesheets applied over your content; they never change your
state or routes. The tier system is on
[Change the appearance](index.md).

## See another example

The [theme catalog](../../reference/themes.md) previews all twenty, and
[Finish and test an app](../../tutorials/finishing.md) picks one for a
real project.

## Look it up

[Site configuration](../../reference/site-config.md) for
`set_website_style` and its relatives.

## Fix a problem

A bad theme name produces a friendly error with suggestions; for
anything odder, start at
[Troubleshooting](../../help/troubleshooting.md).
