---
page_type: index
title: Playground
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Run and edit many small programs.
---

# Playground

Pages full of tiny programs, each running live and each editable in
place. Change the code, run it again, see what happens; nothing you
do here can break anything, and reloading the page resets every
demo.

The playground is for *tinkering*: no walkthroughs, minimal prose,
one idea per demo. When a demo makes you want the full story, it
links out to the page that tells it.

## Collections

- [Basics](basics.md): hello pages, counters, connecting pages.
- [Forms](forms.md): every core input type, in miniature.
- [Lists and tables](lists-and-tables.md): showing collections of
  data.
- [Styling](styling.md): themes, helpers, keywords, and CSS, side by
  side.
- [Images and media](media.md): pictures, plots, sound, and video.
- [Interactive](interactive.md): events, fragments, and timers.
- [Camera, location, and sound](sensors.md): device features (these
  ask for permissions).

## A note on speed

All the demos on one page share a single Python runtime, so the
first demo you run pays the startup cost and the rest are quick.
If a page has many demos, give the first click a moment.

## How to tinker well

1. Predict before you run: say what you expect out loud, then check.
2. Change one thing at a time; when a change surprises you, that is
   the interesting part.
3. Break things on purpose: misspell a route, remove a `str()`, and
   read the error you get. Errors met on purpose are easier to fix
   when they arrive by accident, and
   [the error index](../../help/errors/index.md) explains the common
   ones.
