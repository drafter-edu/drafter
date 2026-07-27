---
page_type: how-to
title: The debug panel in depth
level: L2
audience: S
priority: P1
prereqs: [start/debug-panel]
symbols: []
outcome: Use all five debugger tabs.
---

# The debug panel in depth

## Goal

You want to get the full value out of the debug panel: watching
state, replaying history, reading test results, and answering the
question "what is my app actually doing?"

## Before you start

You have met the panel in [See inside your app](../start/debug-panel.md).
This page goes tab by tab. The panel appears under your app whenever
debug mode is on, which is the default during development;
`hide_debug_information()` removes it for
[release](../your-project/deploy/prepare.md).

## Current: what the app is, right now

The Current tab shows the route that produced the page you are
looking at and the full current state. The state view is live: after
every click it reflects what your routes did.

It is also editable. Changing a value in the state editor and
applying it re-renders the page from the edited state, which is the
fastest way to answer questions like "what does the results page
look like at score 10?" without clicking ten times.

## History: everything that happened

The History tab lists every visit: the route call that ran (with
its actual arguments), the response it produced, and the state
snapshot taken afterward. Expanding a visit's Response shows the returned `Page(...)`
written as Python, which is what
[freezing a page](../add/freeze-pages.md) copies.

Colored markers flag the visits that raised errors or warnings, so
you can scroll back and find the moment something went wrong. The
history can also replay a visit, which re-dispatches the same
request against your current code. Replaying is exactly the check
you want after fixing a bug: does that click work now?

## Overview: the app from above

The routes list shows every registered route with its parameters.
Think of it as a table of contents for your app. Check it when
clicking a button reports that a route does not exist, or when you
suspect a route function is missing its `@route` decorator.
(A visual route graph is planned for this tab but not finished.)

## Tests: your assertions, live

Every assertion that ran at startup is here with its result, line
number, and, for failures, the full difference report. Two buttons
here are more useful than they may first appear: **copy** and
**download**, which export every test the app has run as a
ready-to-save Python file. They become valuable once
[frozen tests](../add/freeze-pages.md) start accumulating.

Tests re-run when your program restarts, not while you click around
the app. If the test list is all green but clicking still breaks
something, the broken behavior does not have a test yet.

## Environment: the machinery

This tab collects several kinds of information about the
environment your app runs in:

- **Files**: what the app's file system holds, for checking that a
  data file or image is actually where `open(...)` expects it.
- **Packages**: which Python packages are loaded.
- **Configuration**: every active setting (title, theme, debug mode,
  and the rest) with its current value, for "did my
  `set_website_...` call actually take?"
- **Runtime info** and **Internals**: versions and wiring, mostly
  useful when [filing a bug report](bug-reports.md).
- **Log**: the cumulative record of errors and warnings, including
  ones that older pages showed and you clicked past.
- **Storage**: saved state slots. Save a situation you want to
  return to (a half-finished quiz, a full shopping cart) and load it
  back later instead of re-clicking your way there.

## The menus

The header menubar above the tabs holds the view controls: an
option to hide the frame, and the live site-theme switcher for
[trying themes](../add/change-appearance/themes.md). It also holds
the Help menu, whose **Download Bug Report** item packages up
[everything a bug report needs](bug-reports.md).

## Common problems

- **The panel is gone**: debug mode is off. Remove or comment out
  `hide_debug_information()` (and any `in_debug_mode=False`), then
  restart.
- **The state view disagrees with the page**: the page was rendered
  before your latest state edit or click; interact once more, or
  check History to see which state each page was built from.
- **Tests show stale results**: tests run at startup. Restart the
  program to re-run them against current code.
- **Editing state broke the page**: you gave a field a value of the
  wrong type, which is a preview of the
  [state type problem](errors/state-mismatch.md). Reset by
  restarting; state edits are never saved to your code.

## Next steps

[Print and the console](printing-and-console.md) adds `print()` and
a live Python prompt to this toolkit, and
[Freeze finished pages](../add/freeze-pages.md) turns the History
tab into a test generator.
