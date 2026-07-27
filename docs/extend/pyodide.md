---
page_type: concept
title: Python in the browser
level: L4
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Hold an accurate deeper runtime model.
---

# Python in the browser

## In one sentence

Your Drafter app runs on a real Python interpreter, called
Pyodide, that has been compiled to run inside a web browser.

## The idea

[How Drafter works](../start/how-drafter-works.md) told you the
honest short version: your program runs twice, and there is no
backend server. This page fills in the machinery.

**Pyodide** is the standard CPython interpreter compiled to
WebAssembly, a format browsers can execute. When someone opens
your app, their browser downloads Pyodide, boots it, and runs
your Python source inside the page. It is not a translation of
your code to JavaScript, and not a lookalike language: it is
Python, with the standard library, running where JavaScript
usually runs.

The two runs, in detail:

1. **On your computer.** `python my_app.py` runs your file in
   normal Python. Top-level code executes: imports, dataclass
   definitions, your `assert_` tests. When `start_server(...)` is
   reached, Drafter starts a small local web server whose only
   job is to hand your source code and the Drafter machinery to
   your browser.
2. **In the browser.** The page boots Pyodide and runs your file
   again, top to bottom, inside the browser. This time
   `start_server(...)` does not start a server; it wires your
   routes to the page and renders the first one. Every click from
   then on is a Python function call inside the browser tab.

Deployment removes run number one: compiling produces static
files, and visitors' browsers do run number two all by
themselves.

Two consequences worth internalizing:

- **The boot cost is real.** Downloading and starting a Python
  interpreter takes a few seconds on first load. That cost is
  per-visitor and mostly per-first-visit (browsers cache the
  download); it is the price of needing no server.
- **The filesystem is virtual.** Inside the browser, `open()`
  works, but it reads from an in-memory filesystem containing
  the files bundled with your app, not the visitor's disk.
  Writing a file works too, but the write lands in that same
  in-memory space and vanishes with the tab, the same way state
  does.

## See it

Ask Python where it is running. Locally, this page reports your
operating system; in the running demo below, the same code
reports `emscripten`, the name of the WebAssembly platform:

```python drafter height=200
from drafter import *
from dataclasses import dataclass
import sys


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Where am I?"),
        "This Python is running on: " + sys.platform
    ])


start_server(State())
```

## What this means for your code

- Code before `start_server(...)` runs in both places; write it
  so it is happy in both. Printing and tests are fine (in the
  browser, `print` goes to the debug console).
- Anything the browser forbids, Python cannot do either: no
  reading the visitor's files, no opening network sockets, no
  running other programs.
- Bundled data files (via `--additional-paths` at compile time)
  are the way to ship data with your app; they appear in the
  virtual filesystem where `open()` finds them.
- A `js` module exists inside Pyodide for calling browser
  JavaScript from Python. It is powerful and sharp-edged; the
  planned JavaScript interop page will cover it properly.

## Where people get confused

- "It's slow" usually means the one-time boot, not your code.
  After boot, route calls are ordinary in-memory function calls,
  faster than a network round trip would be.
- Saving a file appears to work, which suggests it persisted. It
  did not; it went to tab memory.
- The browser's developer console shows JavaScript errors from
  the page's machinery. Your Python errors show up in Drafter's
  own error display and debug console instead.

## Go deeper

- [Third-party libraries](packages.md): how packages arrive in
  the browser.
- [Security honestly](security.md): what this architecture means
  for secrets.
- [Developer architecture docs](../dev/architecture.md): the full
  internal story, including the bridge and client server.
- [Pyodide's own documentation](https://pyodide.org/): the
  project Drafter builds on.
