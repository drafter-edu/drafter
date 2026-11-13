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

Your app works, and now you want it to look the way you imagine.

## Before you start

You should already know how to build pages. If not, start with
[Build your first app](../../start/first-app.md).

## What is CSS?

CSS, short for Cascading Style Sheets, is the language that describes
how a web page looks. The same Python built both of these pages:

<div class="drafter-pagepair" role="img" aria-label="The same page shown twice. Without CSS it is plain black text with a small gray button. With CSS the header is purple with a line under it, the text has room around it, and the button is a solid purple block.">
<div class="drafter-pagepair__page drafter-pagepair__page--plain"><span class="drafter-pagepair__label">Without CSS</span><span class="drafter-pagepair__header">Corgi Fan Club</span><span>Members so far: 12</span><span>Ada approves of this club.</span><span class="drafter-pagepair__button">Reload</span></div>
<div class="drafter-pagepair__page drafter-pagepair__page--styled"><span class="drafter-pagepair__label">With CSS</span><span class="drafter-pagepair__header">Corgi Fan Club</span><span>Members so far: 12</span><span>Ada approves of this club.</span><span class="drafter-pagepair__button">Reload</span></div>
</div>

Your Python decides what is on the page: a header, two lines of text,
and a button. CSS decides how each of those looks. Every Drafter page
you have made was already styled with CSS that Drafter wrote for you,
and now you get to change it.

## What CSS is used for

CSS can change almost anything about how a page looks, but four jobs
cover most of what you will want:

<div class="drafter-samples">
<div class="drafter-sample"><div class="drafter-sample__view"><div style="color: crimson">Lives remaining: 3</div></div><div class="drafter-sample__caption"><b>Color</b><code>color</code>, <code>background-color</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="border: 2px solid slateblue; padding: 2px 8px">Lives remaining: 3</div></div><div class="drafter-sample__caption"><b>Borders</b><code>border</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="background-color: lavender; padding: 12px">Lives remaining: 3</div></div><div class="drafter-sample__caption"><b>Spacing</b><code>padding</code>, <code>margin</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="font-family: Georgia; font-size: 1.15em">Lives remaining: 3</div></div><div class="drafter-sample__caption"><b>Text</b><code>font-family</code>, <code>font-size</code></div></div>
</div>

Each job comes down to one or two CSS properties, named under each
sample. [Design basics](design-basics.md) takes them one at a time.

## Same page, different CSS

A theme is a complete set of CSS that somebody else wrote. In this
program, the highlighted line is the only one about appearance.
Change `"sakura"` to `"retro"`, `"98"`, or `"terminal"` and run it
again:

```python drafter hl_lines="3" height=300
from drafter import *

set_website_style("sakura")


@route
def index() -> Page:
    return Page([
        Header("Corgi Fan Club"),
        "Members so far: 12\n",
        "Ada approves of this club.\n",
        Button("Reload", "index")
    ])


start_server()
```

## Three ways to style a Drafter site

Drafter gives you three ways to change the CSS, listed here from
least effort to most control:

| Way | What it changes | Where to learn it |
| --- | --------------- | ----------------- |
| A theme | The whole site, in one line | [Use a theme](themes.md) |
| Styling functions and keywords | One component at a time | [Styling functions and keywords](helpers.md) |
| Custom CSS | Everything a rule matches | [Custom CSS](custom-css.md) |

Start at the top and move down only when the row above cannot do what
you want. A good rule of thumb is a theme for the whole site, then
functions and keywords for moments of emphasis. If you find yourself
styling every single component by hand, step back and pick a
different theme instead.

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
