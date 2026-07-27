---
page_type: how-to
title: Change the appearance
level: L2
audience: S
priority: P0
prereqs: [start/first-app]
symbols: []
outcome: Choose a styling approach and get quick wins.
---

# Change the appearance

## Goal

Your app works, and now you want it to look better, with the least
effort that gets the look you want.

## Before you start

You should already understand how to build pages; if not, start with
[Build your first app](../../start/first-app.md).

Drafter offers three tiers of styling, in order of
effort. Start at the top and only go deeper when the tier above cannot
do what you want:

1. **[Use a theme](themes.md)**: a single line of code restyles the
   whole site, and there are twenty ready-made looks to choose from.
   Start here.
2. **[Styling functions and keywords](helpers.md)**: make one component
   bold, colored, bigger, or centered. Use these for emphasis and small
   adjustments.
3. **[Custom CSS](custom-css.md)**: write real CSS classes and rules
   when you want a look of your own. Learn
   [design basics](design-basics.md) first.

## Pick a Theme, Any Theme

Picking a theme is the fastest visible improvement. Here is a plain
page with a theme applied. Change `"sakura"` to `"retro"`, `"98"`, or
`"terminal"` in the demo and run it again to see the difference:

```python drafter height=340
from drafter import *
from dataclasses import dataclass

set_website_style("sakura")


@dataclass
class State:
    signups: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Corgi Fan Club"),
        "Members so far: " + str(state.signups) + "\n",
        "Ada approves of this club.\n",
        Button("Join the club", "join")
    ])


@route
def join(state: State) -> Page:
    state.signups = state.signups + 1
    return index(state)


start_server(State(0))
```

One line, `set_website_style("sakura")`, placed right after the imports,
restyles everything: text, buttons, headers, spacing.

## Then adjust individual pieces

After a theme sets the overall look, use styling helpers for the details
you want to stand out:

```python drafter height=280
from drafter import *
from dataclasses import dataclass

set_website_style("simple")


@dataclass
class State:
    lives: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Danger Zone"),
        bold(change_color("Lives remaining: " + str(state.lives), "crimson")),
        "\n",
        Button("Lose a life", "lose_life")
    ])


@route
def lose_life(state: State) -> Page:
    if state.lives > 0:
        state.lives = state.lives - 1
    return index(state)


start_server(State(3))
```

The rule of thumb is to use **themes for the whole site and helpers for
moments of emphasis**. If you find yourself styling every single
component by hand, step back and pick a different theme instead.

## Common problems

- **Nothing changed**: `set_website_style(...)` must run before
  `start_server(...)`. Put it right after the imports.
- **A misspelled theme name**: Drafter lists the valid names in the
  error, with a did-you-mean suggestion.
- **The theme fights your custom look**: themes style everything, so
  heavy customization on top of a strong theme gets messy. Use
  `set_website_style("none")` for a blank slate, then
  [custom CSS](custom-css.md).

## Understand it

Styling changes how things look, never what the app remembers or does.
[How Drafter works](../../start/how-drafter-works.md) explains that
separation.

## See another example

The [theme catalog](../../reference/themes.md) shows every theme, and
[Finish and test an app](../../tutorials/finishing.md) does a full
styling pass on a real project.

## Look it up

[Site configuration](../../reference/site-config.md) for
`set_website_style`, and
[Styling functions](../../reference/styling-functions.md) for every
helper.

## Fix a problem

If a page will not display after styling changes, see
[Troubleshooting](../../help/troubleshooting.md); styling mistakes
usually show as a friendly error naming the bad value.
