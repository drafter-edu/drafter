---
page_type: error
title: A library import fails in the browser
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Fix a library import that fails in the browser.
error_text: "ModuleNotFoundError"
---

# A library import fails in the browser

## The error

```text
ModuleNotFoundError: No module named 'requests'
```

Drafter's friendly layer titles it "Module Not Found". The
signature version of this problem: the import works when you run
the file on your computer, then fails in the browser (or the other
way around).

## What it means

Your app runs on a Python that lives inside the browser, with its
own set of available packages: many scientific and pure-Python
libraries work, some (especially ones needing network or system
access) do not exist there. An `import` your computer's Python can
satisfy is not automatically satisfiable in the tab.

## Where to look

The `import` line named in the traceback, top of your file.

## Check

- **A typo or a self-import**: misspelled module name, or one of
  your own files whose name does not match the import. Same fix as
  ever, no browser involved.
- **A real package that exists for the browser**: common libraries
  like `matplotlib` and `pandas` are available and load on demand;
  first use can take a moment.
- **A package that cannot run in a browser**: libraries built on
  sockets, subprocesses, or C extensions without browser builds.
  `requests` is the famous one; plain use fails because browsers
  gate network access.

## Fix

For the misspelling, fix the name. For browser-capable packages,
import and use them normally; if the deployed site cannot find one
your own machine had, declare it so the build knows to include it
(see [Third-party libraries](../../extend/packages.md)). For
browser-incapable packages, the honest fix is designing around
them; the [Extend section](../../extend/packages.md) covers what
works, what does not, and the substitutions (including how network
fetching actually works from a browser).

## Confirm

Reload the site and watch the console during startup; the import
succeeds and your app reaches its first page.

## Prevent

Test imports in the running site early, not just on your computer;
the two Pythons agree on the language and differ on the toolbox.
Before building a project around a library, spend five minutes
confirming it loads in a Drafter app.

## Understand

[Python in the browser](../../extend/pyodide.md) explains the
runtime; [Third-party libraries](../../extend/packages.md) is the
practical guide.
