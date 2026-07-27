---
page_type: how-to
title: Performance
level: L4
audience: S
priority: P2
prereqs: [extend/pyodide]
symbols: []
outcome: Keep apps responsive.
---

# Performance

## Goal

Know what actually makes a Drafter app slow, so you fix the real
cause instead of guessing. There are only a few causes, and they
are predictable.

## Before you start

One calibration: after the first load, a route call is an
in-memory function call, usually finishing in a millisecond or
two. Student apps are almost never slow because "Python is
slow"; they are slow for one of the four reasons below.

## The first load is not your fault

Downloading and booting Pyodide takes a few seconds, plus more
for heavy libraries like matplotlib or pandas.
([Python in the browser](pyodide.md) explains why.) You cannot
code this away, but you can be honest about it: the loading
screen exists, later visits are faster thanks to caching, and
trimming an unused heavy import is the one real win available.

## Big state is copied often

Drafter snapshots state for history and the back button, so a
huge state gets copied on every route call. Lists of dataclasses
in the hundreds are fine; the usual offenders are media
accidentally stored wholesale:

- Many [Picture](../reference/data-types/picture.md) values, or
  a few enormous ones: `resize` photos down to display size
  when they enter state.
- A growing list of [recordings](../reference/data-types/audio-types.md):
  keep the latest, or offer a
  [Download](../reference/components/input/download.md) instead
  of a collection.
- An append-only log nothing reads: cap it or drop it.

The debug panel's Current tab doubles as a scale: when the state
display itself scrolls for pages, routes are paying to copy all
of it.

## Enormous pages render slowly

A page with thousands of components (one per row of a big
dataset, say) takes noticeable time to build and insert. Show a
slice: the first 25 rows and a "show more" button, or a
per-category page. Nobody reads a 3,000-row table; the browser
still has to build one.

## High-frequency events do full work

An `on_input` or tick route that returns a whole `Page` rebuilds
everything on every keystroke or second. For frequent events,
return a [Fragment](../reference/fragment.md) aimed at the one
region that changes, or an `Update` when nothing visible
changes; that is the difference between redrawing a scoreboard
and redrawing the stadium.
[Live updates](../concepts/live-updates.md) covers choosing.

## Common problems

- **"Slow" only on the first visit**: that is the boot cost.
  Check whether a heavy library is imported but barely used.
- **Clicks lag as a session goes on**: state is growing. Find
  what accumulates (the debug panel shows it) and cap or shrink
  it.
- **Typing stutters in a live field**: the event route returns a
  `Page`; switch to a `Fragment` with a target.
- **The deployed site loads slower than local**: deployed
  visitors download everything fresh, and bundled media counts;
  shrink images and audio files before bundling.

## Related

- [Python in the browser](pyodide.md): where the fixed costs
  come from.
- [Add live behavior](../add/live-behavior.md): the fragment
  patterns.
