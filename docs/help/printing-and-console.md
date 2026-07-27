---
page_type: how-to
title: Print and the console
level: L2
audience: S
priority: P1
prereqs: [start/first-app]
symbols: []
outcome: Use print() to see what is happening.
---

# Print and the console

## Goal

You want to use `print()` to see what your app is doing, and you
want a place to experiment with your running program by hand.

## Before you start

You need nothing beyond a running app. `print()` in a Drafter app does not
disappear; it goes to the **Console**, a small terminal-style panel
that appears in the page footer the first time your program prints
(while debug mode is on, which is the default during development).

## Printing from routes

Drop a `print()` into any route and watch the console as you click:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clicks: int


@route
def index(state: State) -> Page:
    print("Rendering index with", state.clicks, "clicks")
    return Page(state, [
        "Clicks: " + str(state.clicks) + "\n",
        Button("Click me", "add_one")
    ])


@route
def add_one(state: State) -> Page:
    print("add_one is running")
    state.clicks = state.clicks + 1
    return index(state)


start_server(State(0))
```

Printed lines also mirror to the browser's developer-tools console,
and messages Python writes to `stderr` (like warnings) appear in
red. The 🖨️ Console button in the footer opens and closes the
panel, with Clear and Hide buttons to tidy up.

Printing is the quickest way to answer two common questions: "did
this route even run?" and "what value actually arrived?" Print the
parameters at the top of the route you suspect, then click the
button that should trigger it.

## The console is a real Python prompt

The console is also a REPL, a prompt where you can type Python code
and run it immediately: type next to the `>>>` prompt and press
Enter. The REPL shares variables with your program, so your `State`
class and route functions are already available:

```text
>>> state = State(clicks=10)
>>> index(state)
Page(state=State(clicks=10), content=['Clicks: 10\n', Button(text='Click me', url='add_one')])
```

Multi-line blocks work (the prompt changes to `...`), and the Up
and Down arrows revisit earlier commands. Calling a route by hand
in the REPL is a fine way to prototype a test before writing the
`assert_state` line in your file.

## Console modes

Where output appears is configurable with the `--console-mode`
command-line flag (or the `DRAFTER_CONSOLE_MODE` environment
variable):

| Mode | What it does |
| ---- | ------------ |
| `auto` (default) | Console panel in the footer, debug mode only. |
| `hover` | A floating console box pinned to the window, visible even in production. |
| `toast` | Each printed line pops up briefly as a corner notification. |
| `devtools` | No on-page console; output goes only to the browser developer tools. |

To run a production site that still shows printed output, use
`drafter my_site.py --production --console-mode hover`.

## Common problems

- **Nothing prints**: either the route did not run (check that the
  button is wired to it), or you are looking in the wrong place:
  perhaps at the browser console while the output went to the
  footer panel, or the other way around.
- **The console is gone in production**: that is how the `auto`
  mode is designed to behave; `hide_debug_information()` hides the
  footer. Output still reaches the browser's developer tools, or
  you can choose a more visible mode from the table above.
- **Prints flood the console**: a `print` inside a route that runs
  on every keystroke (`on_input`) or on every render will produce a
  line every time. Move the `print` inside the branch you care
  about, and remove debugging prints once they have told you what
  you needed to know.

## Next steps

The [debug panel](debug-panel.md) shows state and history without
any printing. Between the panel and the console, you have a tool
for most "what is happening?" questions.
