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
looking at, a list titled "Errors & Warnings" for that page, and the
full current state. Each field of the state appears with its value
and its type. The state view is live, so after every click it shows
what your routes did. Expanding **Page Content** shows the page
written as an `assert_equal` test.

The state view is read-only. To see a page at a particular state,
such as the results page at score 10, either change the starting
value in `start_server(...)` and save, or click your way to that
state once and keep it with the
[Save/Load menu](#saveload).

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
colors a swatch. Expanding **Page shown** gives an `assert_equal`
test for the visit, with the returned `Page(...)` written as Python,
which is what [freezing a page](../add/freeze-pages.md) copies. The
state after the visit appears below the test.

Ten visits show at first, and the **Show older visits** button adds
the next ten without losing your place. Each line also has a
**Revisit** button, which runs the same route again with the same
arguments and the state as it is now. Revisiting is a quick check
after you fix a bug, because it repeats the click that failed.
**Clear History** asks you to confirm and then empties the list.

When the same problem happens again, the Current tab's list does
not grow a second line; the problem gets a counter such as ×3. The
browser tab's title also carries the number of errors and warnings
on the current page, so a problem shows even when you have switched
to another tab.

## Overview: the app from above

The **Registered Routes** list shows every route in your program
with its parameters, such as `index(state: State)`. Think of the
list as a table of contents for your app. Check it when clicking a
button reports that a route does not exist, or when you suspect a
route function is missing its `@route` decorator.

## Tests: your assertions, live

Every assertion in your file is listed here with its result and its
line number, and each failure has the full difference report. A
failing test also puts a count next to the tab's name.

Tests run again every time the site reloads, which includes every
time you save your file. They do not run while you click around the
app. If every test passes and clicking still breaks something, the
broken behavior does not have a test yet.

The **Regression Tests** section has two buttons, **Copy Regression
Tests** and **Download Tests (.py)**. Both produce one
`assert_equal` test for each page you have visited, in the order you
visited them. A visit whose state has a circular reference gets a
`# Not frozen:` comment in place of its test, because such a state
cannot be written as Python code.
[Freeze finished pages](../add/freeze-pages.md)
explains what to do with those tests.

## Environment: the machinery

This tab collects several kinds of information about the
environment your app runs in.

- **File Systems** lists the files that Python can see in the
  browser, under "Client File System". Press Refresh to update the
  list. Use it to check that a data file is where `open(...)`
  expects it. While your app runs from your own computer, a second
  list, "Host File System", shows the files in your project folder.
  Click a folder there to look inside it, and `../` to go back up.
  A deployed site has no such folder, so that list does not appear
  there.
- **Installed Packages** lists the Python packages that are loaded.
- **Configuration** lists every setting, such as the title, the
  theme, and debug mode, with its current value. Look here to check
  that a `set_website_...` call took effect. Each setting also has
  an Edit button that overrides the value in this browser only.
- **Runtime Info** gives the browser and Python versions, which are
  mostly useful when [filing a bug report](bug-reports.md).
- **Event Log** is a running list of what Drafter has done since the
  site loaded. Errors stay in this list after you leave the page
  that showed them.
- **Browser Storage** lists what Drafter has saved in this browser,
  including the snapshots from the Save/Load menu. Press Refresh to
  update the list, and use the button at the end of a row to delete
  that entry.

## The menus

The menu bar at the top of the frame around your page has five
menus. The names of the items below are the names on the screen.

### Navigate

- **Home** goes to your `index` page.
- **Reset** puts the state back to its starting value and returns to
  the `index` page.
- **Reload Site** reloads the whole site in the browser.
- **Replay Route** runs the current route again with the same
  arguments. If that route changes the state, the change happens
  again.
- **About** shows a page with the information you gave to
  `set_site_information`.
- **Stop Server…** appears while your app runs from your own
  computer. After you confirm, it shuts down the Drafter program
  running in your terminal or editor, the same as pressing Ctrl+C
  there. The tab stays open, and a page that is already loaded may
  still respond to clicks, because your Python runs in the browser.
  Saving your file no longer reloads the site, and reloading the tab
  fails, until you run your program again. The same control is
  available at your site's address plus `--stop-server`, which helps
  when the debug panel is hidden. Deployed sites have no server to
  stop, so the item does not appear there.

### View

- **Toggle Frame** hides the frame around your page, which includes
  the menu bar and the Console box, so that you can see the page as
  a visitor would. The debug panel keeps its own small **View** menu
  at its top right, and choosing Toggle Frame there brings the frame
  back.
- **Production** hides the debug panel as well as the frame. Reload
  the browser tab to get them back.
- **Switch Theme…** opens the theme switcher for
  [trying themes](../add/change-appearance/themes.md).
- **View Page HTML** opens a read-only window with the HTML that
  Drafter generated for the current page.

### Edit

- **Edit Source** opens your program in an editor inside the
  browser. Pressing **Run** restarts the site with the edited code.
  The edit exists only in that browser tab. The file on your
  computer does not change, so copy anything you want to keep back
  into your own editor.
- **Convert HTML to Drafter…** turns HTML you already have into
  Drafter code. Paste the HTML or choose an `.html` file, press
  Convert, and copy the Python it writes. Read the result before
  you use it, because some HTML has no exact Drafter match. The
  converter is downloaded the first time you use it, so the first
  conversion takes a moment longer than the rest.

### Save/Load

A snapshot records the current state and the route that produced the
current page. Use one to return to a situation that takes many
clicks to reach, such as a half-finished quiz or a full shopping
cart.

- **Quick Save** stores a snapshot in the browser.
- **Save to Slot…** stores a snapshot in one of ten numbered slots.
- **Load Most Recent** restores the newest snapshot. The item shows
  how long ago that snapshot was saved, and it is gray until you
  have saved one.
- **Load from Slot…** lets you pick among the saved snapshots.
- **Download Snapshot…** saves a snapshot as a `.json` file on your
  computer, and **Upload Snapshot…** restores from such a file.

Loading a snapshot brings back the page and the state you saved. A
snapshot also records the state from just before its route ran.
Loading puts that earlier state back and runs the route again, the
same way the browser's Back button returns to a page. For example, a
counter saved at 4 on a page produced by an `add_one` route loads
as 4. If the route does something different each time it runs, such
as picking a random number, the loaded page can differ from the one
you saved.

A snapshot saved by an older version of Drafter does not have the
earlier state. Loading one puts the saved state back and runs the
route on top of it, so that counter loads as 5.

Snapshots are kept by the browser, so they survive a reload of the
tab. Each app has its own slots. Two programs that you run at the
same address, one after the other, do not see each other's
snapshots, and a program that you move or rename starts with empty
slots. Snapshots saved before slots were kept for each app are no
longer offered in this menu. They are still listed under Browser
Storage on the Environment tab, where you can delete them.

If you change the fields of your `State` class after you save,
for example by renaming one, loading the snapshot can fail. The
state then stays as it was, and the Current tab lists an error.

### Help

- **Documentation** opens the Drafter documentation in a new tab.
- **Download Bug Report** packages up
  [everything a bug report needs](bug-reports.md).

## Common problems

- **The panel is gone.** Debug mode is off. Remove or comment out
  `hide_debug_information()` and any `in_debug_mode=False`, then
  save. If you chose Production from the View menu, reload the tab.
- **The menus are gone but the panel is still there.** The frame is
  hidden. Open the **View** menu at the top right of the debug panel
  and choose Toggle Frame.
- **The state view disagrees with the page.** A page shows the state
  as it was when its route ran. Check the History tab to see which
  state each page was built from.
- **Tests show old results.** Tests run when the site loads. Save
  your file, or reload the tab, to run them against the current
  code.
- **A loaded snapshot is off by one step.** The snapshot was saved
  by an older version of Drafter. Save it again to get one that
  loads exactly. See the note under [Save/Load](#saveload).
- **Your saved snapshots are gone.** Slots belong to one app at one
  address. See the note under [Save/Load](#saveload).

## Next steps

[Print and the console](printing-and-console.md) adds `print()` and
a live Python prompt to this toolkit, and
[Freeze finished pages](../add/freeze-pages.md) turns the History
tab into a test generator.
