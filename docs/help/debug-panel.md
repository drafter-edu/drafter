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

The History tab lists every visit, newest first, one line each.
The line starts with how the visit went (**Success**, **1 warning**,
**Error**, or **Page not found**), then the time, then the call that
ran written the way you would write it, such as
`save(size=60, name='Ada')`. Pictures and files show as a short
summary like `<Picture ada.png 640×480>` instead of their raw data,
and a warning or error puts its first line on the right of the row.

Expanding **Where these values came from** lists each argument: the
form field, button argument or default it came from, what arrived,
and what Drafter converted it to (a form sends `'60'`; your `int`
parameter receives `60`). Uploaded pictures get a thumbnail and
colors a swatch. Expanding **Page shown** gives the returned
`Page(...)` written as Python, which is what
[freezing a page](../add/freeze-pages.md) copies, and the state
after the visit.

Ten visits show at first; **Show older visits** adds the next ten
without losing your place. The history can also replay a visit,
which re-dispatches the same request against your current code.
Replaying is exactly the check you want after fixing a bug: does
that click work now?

When the same problem happens again, the Current tab's list does
not grow a second line; the problem gets a counter such as ×3. The
browser tab's title also carries the number of errors and warnings
on the current page, so a problem shows even when you have switched
to another tab.

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

The Edit menu's **Convert HTML to Drafter…** item turns HTML you
already have into Drafter code. Paste the HTML (or choose an `.html`
file), press Convert, and copy the Python it writes. The result is a
starting point: read it before using it, because some HTML has no
exact Drafter match. The converter downloads the first time you use
it, so the first conversion takes a moment longer than the rest.

While your app runs from your own computer, the Navigate menu ends
with **Stop Server…**. After you confirm, it shuts down the Drafter
program running in your terminal or editor, the same as pressing
Ctrl+C there. The tab stays open but stops working until you run
your program again. The same control lives at your site's address
plus `--stop-server`, which is handy when the debug panel is
hidden behind a small frame. Deployed sites have no server to stop,
so the item does not appear there.

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
