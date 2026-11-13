---
page_type: concept
title: Design basics
level: L2
audience: S
priority: P1
prereqs: [add/change-appearance]
symbols: []
outcome: Apply spacing, color, and typography deliberately.
---

# Design basics

## In one sentence

Every component on the page is a box, and a handful of CSS properties
decide how each box looks.

## The idea: every component is a box

Imagine every component on the page as a box, even the ones that do
not look like one. A line of text is a box. So is a button, a
picture, and a header. Every box is built from the same four layers:

<div class="drafter-boxmodel">
<div class="drafter-boxmodel__picture" role="img" aria-label="Four boxes nested inside each other. From the outside in they are the margin, the border, the padding, and the content, which reads: Ada is a corgi.">
<div class="drafter-boxmodel__layer drafter-boxmodel__layer--margin"><span>margin</span>
<div class="drafter-boxmodel__layer drafter-boxmodel__layer--border"><span>border</span>
<div class="drafter-boxmodel__layer drafter-boxmodel__layer--padding"><span>padding</span>
<div class="drafter-boxmodel__content">Ada is a corgi.</div>
</div>
</div>
</div>
</div>
<div class="drafter-boxmodel__key">
<span style="--drafter-key: var(--drafter-box-content)"><b>Content</b>: the thing itself, such as text or a picture.</span>
<span style="--drafter-key: var(--drafter-box-padding)"><b>Padding</b>: space inside the border, around the content.</span>
<span style="--drafter-key: var(--drafter-box-border)"><b>Border</b>: a line drawn around the padding.</span>
<span style="--drafter-key: var(--drafter-box-margin)"><b>Margin</b>: space outside the border that holds neighbors away.</span>
</div>
</div>

## Some layers are zero

Every box has all four layers, but any of them can be zero thick.
Here are four boxes with typical numbers:

<div class="drafter-boxlineup">
<div class="drafter-boxlineup__item"><div class="drafter-boxlineup__stage"><span class="drafter-boxlineup__box" style="--m: 0; --b: 0; --p: 0" role="img" aria-label="A box that is only its content, with nothing around it."><span><span><span>Ada is a corgi.</span></span></span></span></div><span class="drafter-boxlineup__name">Plain text</span><span class="drafter-boxlineup__values">margin 0<br>border 0<br>padding 0</span></div>
<div class="drafter-boxlineup__item"><div class="drafter-boxlineup__stage"><span class="drafter-boxlineup__box" style="--m: 0.3; --b: 0.15; --p: 0.45" role="img" aria-label="A box with a thin margin, a thin border, and some padding around its content."><span><span><span>Feed Ada</span></span></span></span></div><span class="drafter-boxlineup__name">A button</span><span class="drafter-boxlineup__values">margin 4px<br>border 2px<br>padding 6px</span></div>
<div class="drafter-boxlineup__item"><div class="drafter-boxlineup__stage"><span class="drafter-boxlineup__box" style="--m: 0.6; --b: 0.15; --p: 0.9" role="img" aria-label="A box with a wide margin, a thin border, and generous padding around its content."><span><span><span>Field trip on Friday!</span></span></span></span></div><span class="drafter-boxlineup__name">A notice</span><span class="drafter-boxlineup__values">margin 8px<br>border 2px<br>padding 12px</span></div>
<div class="drafter-boxlineup__item"><div class="drafter-boxlineup__stage"><span class="drafter-boxlineup__box" style="--m: 0.6; --b: 0.45; --p: 0" role="img" aria-label="A picture with a wide margin and a thick border touching it, with no padding between."><span><span><span class="drafter-boxlineup__photo"></span></span></span></span></div><span class="drafter-boxlineup__name">A framed picture</span><span class="drafter-boxlineup__values">margin 8px<br>border 6px<br>padding 0</span></div>
</div>

Plain text has no padding, border, or margin at all. A button has a
little of each, which is most of why it looks like a button.

## See it: one box, layer by layer

This program builds one box, then gives it a fill, padding, a border,
and a margin, one highlighted line each. The next page explains these
functions. For now, change a number and run it again to watch that
layer grow:

```python drafter hl_lines="7-10" height=300
from drafter import *


@route
def index() -> Page:
    box = Div("Ada is a corgi.")
    box = change_background_color(box, "lavender")
    box = change_padding(box, "20px")
    box = change_border(box, "4px solid slateblue")
    box = change_margin(box, "30px")
    return Page([
        "The line above the box.",
        box,
        "The line below the box."
    ])


start_server()
```

## Color: the text and the fill

Two properties do most of the work. `color` is the foreground, the
text itself. `background-color` is the fill behind the content and
its padding:

<div class="drafter-samples">
<div class="drafter-sample"><div class="drafter-sample__view"><div style="color: crimson">Lives remaining: 3</div></div><div class="drafter-sample__caption"><code>color: crimson</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="background-color: lavender">Lives remaining: 3</div></div><div class="drafter-sample__caption"><code>background-color: lavender</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="color: white; background-color: slateblue">Lives remaining: 3</div></div><div class="drafter-sample__caption"><code>color: white</code><br><code>background-color: slateblue</code></div></div>
</div>

One main color and one accent go a long way, and the text always has
to stand out clearly from what is behind it. The names come from the
[color table](../../reference/colors.md).

## Borders

`border` draws the line between the padding and the margin. Its value
has three parts: how thick, what kind of line, and what color:

<div class="drafter-samples">
<div class="drafter-sample"><div class="drafter-sample__view"><div style="border: 1px solid black; padding: 4px 10px">Ada is a corgi.</div></div><div class="drafter-sample__caption"><code>border: 1px solid black</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="border: 4px dashed crimson; padding: 4px 10px">Ada is a corgi.</div></div><div class="drafter-sample__caption"><code>border: 4px dashed crimson</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="border: 6px double slateblue; padding: 4px 10px">Ada is a corgi.</div></div><div class="drafter-sample__caption"><code>border: 6px double slateblue</code></div></div>
</div>

The kinds of line you will use most are `solid`, `dashed`, `dotted`,
and `double`.

## Spacing: padding and margin

`padding` is the space inside the border, and `margin` is the space
outside it. Padding takes the box's fill, while margin is always
see-through, which is how to tell them apart on screen:

<div class="drafter-samples">
<div class="drafter-sample"><div class="drafter-sample__view"><div style="border: 2px solid slateblue; background-color: lavender; padding: 0; margin: 0">Ada</div><div style="border: 2px solid slateblue; background-color: lavender; padding: 0; margin: 0">Babbage</div></div><div class="drafter-sample__caption"><code>padding: 0</code><br><code>margin: 0</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="border: 2px solid slateblue; background-color: lavender; padding: 10px; margin: 0">Ada</div><div style="border: 2px solid slateblue; background-color: lavender; padding: 10px; margin: 0">Babbage</div></div><div class="drafter-sample__caption"><code>padding: 10px</code><br><code>margin: 0</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="border: 2px solid slateblue; background-color: lavender; padding: 10px; margin: 10px">Ada</div><div style="border: 2px solid slateblue; background-color: lavender; padding: 10px; margin: 10px">Babbage</div></div><div class="drafter-sample__caption"><code>padding: 10px</code><br><code>margin: 10px</code></div></div>
</div>

When a page feels wrong and you cannot say why, the answer is usually
"not enough space."

## Text: typeface and size

`font-family` picks the typeface, and `font-size` sets how big the
letters are:

<div class="drafter-samples">
<div class="drafter-sample"><div class="drafter-sample__view"><div style="font-family: Georgia">Ada is a corgi.</div></div><div class="drafter-sample__caption"><code>font-family: Georgia</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="font-family: monospace">Ada is a corgi.</div></div><div class="drafter-sample__caption"><code>font-family: monospace</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="font-size: 12px">Ada is a corgi.</div></div><div class="drafter-sample__caption"><code>font-size: 12px</code></div></div>
<div class="drafter-sample"><div class="drafter-sample__view"><div style="font-size: 28px">Ada is a corgi.</div></div><div class="drafter-sample__caption"><code>font-size: 28px</code></div></div>
</div>

Sizes should mean something: one page title, section headings below
it, and body text below that. Typefaces that are safe to use are in
the [font list](../../reference/fonts.md).

## What this means for your code

- Apply a [theme](themes.md) first. Themes already make most of these
  choices well, so your main job becomes not fighting them.
- Reach for space before decoration: more padding or margin fixes more
  pages than a new color does.
- Keep a tiny palette: pick two colors from the
  [color table](../../reference/colors.md) and use only those.

You have now met seven properties: `color`, `background-color`,
`border`, `padding`, `margin`, `font-family`, and `font-size`. Each
one has a Drafter function and a keyword, and
[Styling functions and keywords](helpers.md) is where you set them.

## Where people get confused

- **"Making it pretty means adding things."** Usually it means
  removing: fewer colors, fewer font sizes, more space.
- **"Margin and padding are the same."** Margin pushes neighbors
  away; padding pushes your own border away from your content. A
  background color fills padding but not margin, which is how to
  tell them apart on screen.
- **"It looks fine on my screen."** Your screen is only one of many
  sizes. Narrow the window and watch what happens: capped line
  widths and flexible layouts (see
  [Row](../../reference/components/layout/row.md)) hold up when the
  window shrinks.

## In more depth

The box and its properties are the tools. Good-looking pages come from
a few teachable habits in how you use them (generous space, restrained
color, and clear text hierarchy) rather than from talent. Visual
design has rules the way code does, and the beginner-sized set fits
here.

### Space is a tool, not waste

Crowded pages feel broken even when they work. Give elements room
with margin and padding, group related things close together, and let
unrelated things drift apart.

### Color needs restraint

One main color plus one accent goes a long way, while a page with six
colors has no clear emphasis at all. Two hard rules come with color.
First, text must contrast strongly with its background; squint at the
page, and if the text fades for you, it will fade for your users.
Second, color can never be the only carrier of meaning, because not
everyone perceives color; pair it with words or symbols, such as
writing "Error: ..." in red rather than relying on red alone.

Check contrast and colorblind-safety once per project. Gray text on a
white background and red-versus-green distinctions are the classic
failures, and meaning carried only by color locks some users out
entirely.

### Typography is hierarchy

Use [Header](../../reference/components/text/header.md) levels in
order for structure, and styling for emphasis. Never use a `Header`
only to make text bigger. Long lines tire the eyes, so if text spans
the whole window, constrain its width (`change_width(..., "40em")` is
a reasonable ceiling).

### The habits at work

This demo shows the same content twice: first crowded, then spaced
and ranked. The only differences are space, one accent color, and
heading levels:

```python drafter hl_lines="16-26" height=420
from drafter import *


def crowded() -> list:
    return [
        Header("Bake Sale", 3),
        Header("Cookies", 3),
        "Chocolate chunk, oatmeal, mystery. All good. Probably.\n",
        Header("When", 3),
        "Saturday.\n"
    ]


def designed() -> list:
    return [
        Header("Bake Sale"),
        change_padding(Div(
            Header("Cookies", 2),
            change_width(
                "Chocolate chunk, oatmeal, mystery. All good. Probably.\n",
                "30em")
        ), "12px"),
        change_padding(Div(
            Header("When", 2),
            change_color(bold("Saturday.\n"), "darkslateblue")
        ), "12px")
    ]


@route
def index() -> Page:
    return Page(
        [Header("Crowded", 4), HorizontalRule()] + crowded() +
        [HorizontalRule(), Header("Designed", 4), HorizontalRule()] +
        designed()
    )


start_server()
```

Compare cause and effect: the designed version ranks its headings
(one at level 1, sections at level 2), boxes each section with
padding, caps the line length, and spends its single accent color
on the one fact that matters most.

## Go deeper

- [Styling functions and keywords](helpers.md) sets these properties
  from Python, one component at a time.
- [Custom CSS](custom-css.md) sets them with real CSS rules.
- [MDN's box model introduction](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Box_model)
  and [web.dev's design basics](https://web.dev/learn/design/)
  continue where this page stops.
- [Improve the design](../../your-project/improve-the-design.md)
  walks through a usability pass for your project.
