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

**Why did my app forget everything when I reloaded?**
Reloading starts the program over, and state lives in memory, so
it is rebuilt from your defaults. This is how Drafter works, not
a bug. [How Drafter works](../start/how-drafter-works.md)
explains, and [State](../concepts/state.md) covers what does and
does not persist.

**Where is my data stored?**
Nowhere permanent. Each visitor's data lives in their own browser
tab while the tab is open. There is no database and no server
holding anything. [How Drafter works](../start/how-drafter-works.md).

**Can other people see what a visitor types into my app?**
No. Every visitor runs a private copy; nothing anyone enters
travels anywhere. The same fact means your app cannot have shared
features like chat or leaderboards.
[Security honestly](../extend/security.md).

**Why is the first load so slow?**
The browser downloads and boots a Python interpreter, one time.
After that, everything is fast.
[Python in the browser](../extend/pyodide.md).

**Why does nothing after `start_server(...)` run?**
`start_server` hands your program over to the browser; lines
after it are not part of the app. Put tests before it and page
logic in routes. [Troubleshooting](troubleshooting.md).

**Why does the back button not undo the visitor's last action?**
Back replays the route that built the previous page with the
state as it is now; it re-runs a function rather than restoring
old data. [State](../concepts/state.md).

**Where did my `print()` output go?**
On your computer, to the console you ran the program in; in the
browser, to the debug panel's console.
[Printing and the console](printing-and-console.md).

**Is my login page secure?**
No. The whole program, password included, is readable by every
visitor. Login pages are good practice at building flows and
must never guard anything real.
[Security honestly](../extend/security.md).

**Can I use dictionaries in my state?**
Yes; dictionaries, sets, and most built-in types store fine. The
documentation's examples stick to lists and dataclasses because
most readers meet those first.

**Why do my changes not show up?**
Usually an unsaved file, a stopped program, or a stale tab, in
that order of likelihood. [Troubleshooting](troubleshooting.md)
has the checklist.

**How do I share my app with someone?**
Deploy it: your app compiles to a static site that GitHub Pages
hosts free, and you send the URL.
[Deploy and submit](../your-project/deploy/index.md). A localhost
URL only works on your own computer while your program runs.

**Can my app fetch data from the internet?**
Often, with the `requests` library, when the data source allows
browser requests. [Third-party libraries](../extend/packages.md)
explains the limits.

**Why does my test fail after I restyled a page?**
Loose `assert_has` tests survive styling; frozen whole-page tests
include it, so re-freeze deliberately restyled pages.
[Test a feature](../add/test-a-feature.md) and
[Freeze finished pages](../add/freeze-pages.md).

**My error is not in the error index. Now what?**
Work symptom-first in [Troubleshooting](troubleshooting.md), and
if you suspect Drafter itself is wrong, the
[bug report guide](bug-reports.md) shows what to send and where.
