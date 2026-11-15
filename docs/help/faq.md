---
page_type: reference
title: FAQ
audience: S
priority: P2
prereqs: []
symbols: []
outcome: Get quick answers, each linking to the full page.
---

# FAQ

Short answers to the questions we hear most, each with a link to
the page that explains properly.

## How Drafter behaves

### Why did my app forget everything when I reloaded?

Reloading starts the program over, and state lives in memory, so
it is rebuilt from the values in `start_server(...)`. This is how
Drafter works, not a bug.
[How Drafter works](../start/how-drafter-works.md) explains, and
[State](../concepts/state.md) covers what does and does not
persist.

### Why did reloading take me back to the first page?

The address bar remembers the last route you visited, in the part
that looks like `?route=save_name`. Reloading starts the app over
and then runs that route again. If the route expects a value from a
form, no form was submitted this time, so Drafter opens the first
page instead and lists a warning in the debug panel that says so.
Nothing in your code needs fixing. A
route that needs only the state is run again after a reload, with
the state back at its starting value.
[Reloading the tab](troubleshooting.md#reloading-the-tab-shows-a-page-i-did-not-expect)
has the details.

### Where is my data stored?

Nowhere permanent. Each visitor's data lives in their own browser
tab while the tab is open. There is no database and no server
holding anything. [How Drafter works](../start/how-drafter-works.md).

### Can my app save data between visits?

Not by itself. An app can offer the visitor their data as a file to
download, and read that file back in on a later visit.
[Save and load your data](../add/files.md#recipe-save-and-load-your-data)
is a complete recipe.

### Can other people see what a visitor types into my app?

No. Every visitor runs a private copy, and nothing anyone enters
travels anywhere. The same fact means your app cannot have shared
features like chat or leaderboards.
[Security honestly](../extend/security.md).

### What does the browser's Back button do?

Back shows the earlier page again, with the data as it was then.
Drafter restores the state from just before that page's route ran,
and then runs the route again to rebuild the page. A counter that
shows 3 shows 2 after Back. Because the route really does run
again, a route that picks a random number can show a different
result from the first time. [State](../concepts/state.md).

### Why is the first load so slow?

The browser downloads and boots a Python interpreter, one time.
After that, everything is fast.
[Python in the browser](../extend/pyodide.md).

### Why does nothing after `start_server(...)` run?

On your computer, `start_server` keeps running for as long as the
site is up, so Python does not reach the lines after it until the
server stops. Drafter prints a warning when it finds code there. Put
tests and settings before it and page logic in routes.
[Code after start_server never runs](errors/nothing-after-start-server.md).

## Writing your app

### Why is everything on one line?

Drafter does not start a new line between the items in a page's
content list. End a string with `"\n"` where you want the next item
to begin on a new line, as in `"Your score: 5\n"`.
[Page](../reference/page.md) lists the content rules.

### How do I put things side by side?

Wrap them in a `Row`, which lays its contents out from left to
right. [Row](../reference/components/layout/row.md).

### Why does `input()` not work the way it does in my other programs?

Inside a route, `input()` opens a pop-up box in the browser that
shows your question, and the page waits until the box is answered.
Pressing Cancel gives an empty string. A web page asks for
information with form components instead: show a `TextBox` and a
`Button`, and receive the answer as a parameter of the next route.
[Ask the user for information](../add/ask-for-information.md).

### Why does `time.sleep()` not make my page wait and then change?

A page appears only after its route returns. `time.sleep(3)` makes
the route take three seconds longer, and the visitor sees nothing
new during that time. To change the page later, or again and again,
use a `Timer`. [Make things happen over time](../add/timers.md).

### Where did my `print()` output go?

Output printed by a route appears on the web page, in the box
labeled Console below your app. It does not appear in Thonny's
shell, because routes run in the browser. The shell shows only what
was printed while the program was starting, such as test results.
[Printing and the console](printing-and-console.md).

### Can I use dictionaries in my state?

Yes. Dictionaries, sets, and most built-in types can be stored.
The documentation's examples use lists and dataclasses because
most readers meet those first.

### Can I split my program into more than one file?

Yes. Put helper functions in a second `.py` file in the same
folder and import them.
[Split your program across files](../add/files.md#recipe-split-your-program-across-files)
covers the details, including what to upload when you deploy.

### Can my app fetch data from the internet?

Often, with the `requests` library, when the data source allows
requests from a browser.
[Third-party libraries](../extend/packages.md) explains the limits.

### Why do my changes not show up?

While your program is running, saving the file reloads the site in
the browser. If nothing changed, the usual causes are a program
that has stopped, a syntax error in the file you saved (a box on
the page says so, and the last working version keeps running), or
an edit made to a different file from the one that is running.
[Troubleshooting](troubleshooting.md) has the checklist.

## Testing and errors

### Why does my test fail after I restyled a page?

Assertions ignore styling by default, so a new color, font, or
theme does not change any test result. If a test did change, the
restyle also changed the page's words, their order, or the kind of
component, for example by turning plain text into a `Header`.
[Test a feature](../add/test-a-feature.md) and
[Freeze finished pages](../add/freeze-pages.md).

### My error is not in the error index. Now what?

Look the error up by the title at the top of the error page first.
If it is not listed, work from the symptom in
[Troubleshooting](troubleshooting.md). If you suspect Drafter
itself is wrong, the [bug report guide](bug-reports.md) shows what
to send and where.

## Sharing your app

### How do I share my app with someone?

Deploy it. Your app compiles to a static site that GitHub Pages
hosts for free, and you send the URL.
[Deploy and submit](../your-project/deploy/index.md). A localhost
URL only works on your own computer while your program runs.

### How do I hide the debug panel?

Call `hide_debug_information()` near the top of your program,
before your routes.
[Prepare for release](../your-project/deploy/prepare.md) lists it
with the other release settings.

### Does my app work on a phone?

A deployed app runs in a phone's browser the same way it runs on a
computer. Pages that looked fine in a wide window can be cramped
on a small screen, so open your deployed site on a phone before
you share it.
[Improve the design](../your-project/improve-the-design.md).

### Is my login page secure?

No. The whole program, password included, is readable by every
visitor. Login pages are good practice at building flows and
must never guard anything real.
[Security honestly](../extend/security.md).
