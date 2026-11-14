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

An `import` that works on your computer and fails in the browser
does not produce an error page. A dialog titled "Error" opens over
the site as it loads. The dialog says "Error running student code",
lists what to try, and ends with a Python traceback whose last lines
look like this:

```text
  File "main.py", line 3, in <module>
    import turtle
ModuleNotFoundError: No module named 'turtle'
The module 'turtle' is removed from the Python standard library in the
Pyodide distribution due to browser limitations.
```

A failed import can appear in two other places:

- **In the terminal, before the site opens**: a Python traceback
  that ends with a line such as
  `ModuleNotFoundError: No module named 'reqests'`. No browser tab
  opens, because the module is missing on your own computer.
- **On an error page titled "Module Not Found"**: this happens when
  the `import` statement is inside a route function, so the failure
  waits until that route runs. The sentence under the title reads
  "Python could not find or load the module 'reqests' that your code
  imports."

## What it means

Your program runs twice. It runs once on your computer to start the
site, and it runs again inside the browser, on a version of Python
built for browsers. Each of the two has its own set of libraries.
When the program starts in the browser, Drafter reads its `import`
lines and installs what they name, first from the libraries built
for the browser and then from PyPI, the same place `pip` uses. The
import fails when nothing can supply a module with that name.

## Where to look

Look at the `import` line named at the end of the traceback, and at
the module name in the last line.

## Check

- **A misspelled name**: `import reqests` in place of
  `import requests`. This usually fails in the terminal first.
- **A library that is not installed on your computer**: the traceback
  is in the terminal and the site never opens. Install the library
  with pip or with Thonny's package manager.
- **A part of Python that the browser does not have**: `turtle` and
  `tkinter` open windows on your own computer's screen, which a web
  page cannot do. The traceback says the module "is removed from the
  Python standard library in the Pyodide distribution".
- **A library with compiled parts and no browser build**: Drafter
  can install a library that is written entirely in Python, or one
  that has been built for the browser. A library that is neither
  cannot be installed, and its import fails with `No module named`.
  [Third-party libraries](../../extend/packages.md#what-works-and-what-cannot)
  describes which kinds of library fall into this group.
- **A library whose install name differs from its import name**:
  Drafter looks for a library by the name on the `import` line. The
  dialog's second suggestion covers this case.
- **One of your own files**: `import helpers` needs a file named
  `helpers.py` next to your program. On a deployed site, that file
  must also be part of the site, as
  [Image or file works locally but 404s when deployed](missing-asset-on-deploy.md)
  explains.

Many well-known libraries do work in the browser. `requests` loads
there, and `matplotlib` and `pandas` have browser builds. The first
page load that needs one of them takes longer while it downloads.

## Fix

The fix depends on the cause:

1. For a misspelling, correct the name. For a library missing from
   your computer, install it.
2. For `turtle`, `tkinter`, or a library with no browser build, no
   setting makes the import work. Build the feature from Drafter's
   own components or from a library that does run in the browser.
3. For a library that installs under a different name, start the
   site with `--project-packages` followed by that name, as
   [Declaring packages explicitly](../../extend/packages.md#declaring-packages-explicitly)
   shows.
4. For one of your own files, put the file next to your program
   under the exact name the `import` line uses.

## Confirm

Save the corrected file and close the dialog. The site reloads and
reaches its first page.

## Prevent

Try a library in a running Drafter site before you build a project
around it. A short program that imports the library and shows one
page is enough to find out whether the browser can load it. The two
Pythons run the same language but offer different libraries.

## Understand

[Python in the browser](../../extend/pyodide.md) explains the
runtime; [Third-party libraries](../../extend/packages.md) is the
practical guide.
