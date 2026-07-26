# Printing and the Console

When you call `print()` in a Drafter application, the output does not just
disappear — it goes to the **Console**, a small terminal-style panel at the
bottom of your website. The very first time your program prints something,
the Console appears in the footer of the page (as long as you are in debug
mode, which is the default while you are developing).

```python
from drafter import *

@dataclass
class State:
    clicks: int

@route
def index(state: State) -> Page:
    print("Rendering the index page with", state.clicks, "clicks")
    return Page(state, [
        Button("Click me!", index)
    ])

start_server(State(0))
```

Every time this route runs, the printed message shows up in the Console at
the bottom of the page (and is also mirrored to your browser's developer
tools console, if you prefer looking there). Error messages that Python
writes to `stderr`, such as warnings, appear in red.

You can also open or close the Console yourself with the **🖨️ Console**
button in the footer bar, and use its **Clear** and **Hide** buttons to tidy
up.

## Running Your Own Commands

The Console is not just for reading — it is a real, interactive Python
prompt (a "REPL"), just like the one you get from running `python` in a
terminal. Type any Python expression next to the `>>>` prompt and press
Enter:

```
>>> 2 + 2
4
>>> state = State(clicks=10)
>>> index(state)
Page(state=State(clicks=10), content=[Button(text='Click me!', url='/')])
```

The prompt shares its variables with your program, so you can inspect your
`State` class, call your route functions directly, and experiment with your
code while the site is running. Multi-line constructs work the way you would
expect: the prompt changes to `...` until you finish the block. Use the Up
and Down arrow keys to revisit commands you typed earlier.

## What About Production Mode?

When your site runs in production mode (for example, after using
`hide_debug_information()` or deploying your site), the footer — and with it
the Console — is hidden. Your `print()` output still goes to the browser's
developer tools console, so nothing is lost.

If you want printed output to be visible in production, you can pick a
different *console mode* with the `--console-mode` command-line flag (or the
`DRAFTER_CONSOLE_MODE` environment variable):

| Mode | What it does |
|------|--------------|
| `auto` (default) | Console panel in the footer, visible in debug mode only |
| `hover` | A floating console box pinned to the bottom of the window, visible even in production |
| `toast` | Each printed line pops up briefly as a small notification in the corner |
| `devtools` | No on-page console at all; output only goes to the browser developer tools |

For example, to run a production site that still shows printed output in a
floating box:

```
drafter my_site.py --production --console-mode hover
```
