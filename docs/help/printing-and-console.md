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

You need a running app with the debug panel showing, which is the
default while you develop. In a Drafter app, the output of `print()`
goes to the **Console**, a dark box on the web page itself, below
your page and above the debug panel. The box appears the first time
your program prints.

## Where print output goes

A Drafter program runs in two places, and each place has its own
output.

- **The terminal, or Thonny's shell.** When you start the program,
  Python runs your file once on your computer. Your tests run during
  that first run, and Drafter builds the first page. Anything
  printed during that run appears in the terminal, including test
  results such as `SUCCESS at line 39 (assert_has)`.
- **The browser.** The browser then runs your file again, and from
  that point on every route runs in the browser. The output goes to
  the Console box on the page. The box also shows the test results
  from the browser's run of your file.

One consequence surprises many people. A `print()` inside a route
runs in the browser when a button is clicked, so its output appears
in the page's Console box and never in the terminal or Thonny's
shell. The same is true after you save a change. The site reloads in
the browser, the tests run again there, and the terminal prints
nothing new.

Every printed line is also copied to the console of the browser's
developer tools, which you can open with ++f12++.

## Printing from routes

Add a `print()` to any route and watch the Console box as you click.

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

The demos on this documentation site show printed lines in a small
Console box that floats at the bottom of the demo. Click
**Click me** to see more lines arrive. When you run the same program
on your own computer, the Console box sits below the page instead.

Messages that Python writes to `stderr`, such as warnings, appear in
the Console box in red. The **Console** button in the bar above the
box opens and closes the box. Inside the box, **Clear** empties it
and **Hide** closes it. After you press Hide, new output does not
reopen the box, so press the Console button to see it again. The
floating box in the demos has no Console button. After Hide, it
comes back the next time something is printed.

Printing is the quickest way to answer two common questions, which
are "did this route run at all?" and "what value arrived?" Print
the parameters at the top of the route you suspect, then click the
button that should trigger it.

## The console is a real Python prompt

The Console box is also a REPL, a prompt where you can type Python
code and run it immediately. Type next to the `>>>` prompt and press
Enter. The REPL shares variables with your program, so your `State`
class and route functions are already available.

```text
>>> state = State(clicks=10)
>>> index(state)
Rendering index with 10 clicks
Page(state=State(clicks=10), content=['Clicks: 10\n', Button('Click me', 'add_one')], target=Target(id='drafter-body--'), css=None, js=None)
```

Calling a route at the prompt runs the route and prints the `Page`
it returns. The page on screen does not change.
Blocks of several lines work, and the prompt changes to `...` while
you are inside one. The Up and Down arrow keys bring back earlier
commands. Calling a route by hand at the prompt is a good way to
try out a test before you write the `assert_equal` line in your
file.

## Console modes

The `console_mode` setting controls where output appears. You can
pass it to `start_server`, as in
`start_server(State(0), console_mode="hover")`. You can also use the
`--console-mode` command-line flag or the `DRAFTER_CONSOLE_MODE`
environment variable.

| Mode | What it does |
| ---- | ------------ |
| `auto` (default) | The Console box under the page, only while the debug panel is showing. |
| `hover` | A floating Console box pinned to the bottom of the window, with or without the debug panel. Hide closes it until the next output is printed. |
| `toast` | Each printed line appears for a few seconds as a small notice in a corner of the window. |
| `devtools` | No Console box on the page. Output goes only to the browser's developer tools. |

In every mode, output is also copied to the browser's developer
tools.

## Printing on a deployed site

A deployed site normally calls `hide_debug_information()`, which
hides the debug panel and the Console box with it. In the default
`auto` mode, visitors see no printed output on the page. The
`print()` calls still run, and their output is still in the
browser's developer tools, where a curious visitor can read it, so
do not print anything private.

To keep printed output visible on a site without the debug panel,
choose the `hover` or `toast` mode, for example with
`start_server(State(0), console_mode="hover")`.

## Common problems

- **Nothing prints in the terminal or Thonny's shell.** Output from
  routes never goes there. Look at the Console box on the web page.
- **Nothing prints in the Console box.** The route may not have run.
  Open the debug panel's History tab and check that clicking the
  button adds a line for the route you expect.
- **The Console box is missing.** The box appears only after
  something has been printed, and only while the debug panel is
  showing. If you pressed Hide, press the Console button under your
  page (in `hover` mode, the box returns with the next output). If
  your program calls `hide_debug_information()`, see
  [Printing on a deployed site](#printing-on-a-deployed-site).
- **Prints flood the console.** A `print` inside a route that runs
  on every keystroke (`on_input`) produces a line every time the
  route runs. Move the `print` inside the branch you care about, and
  remove debugging prints once they have told you what you needed
  to know.

## Next steps

The [debug panel](debug-panel.md) shows state and history without
any printing. Between the panel and the console, you have a tool
for most "what is happening?" questions.
