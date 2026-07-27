---
page_type: reference
title: start_server
level: L1
audience: S
priority: P0
prereqs: []
symbols:
  - start_server
outcome: Know every student-relevant start_server option.
---

# start_server

`start_server(...)` hands your routes over to Drafter and starts the
site. It is the last line of every Drafter program: code written after
it [never runs](../help/errors/nothing-after-start-server.md).

## Syntax

```python
start_server()
start_server(initial_state)
start_server(initial_state, theme="terminal", site_title="My App")
```

The first argument is your starting state, usually an instance of your
`State` dataclass. Leave it out for an app with no state.

```python drafter height=200
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        Button("Add a point", "gain")
    ])


@route
def gain(state: State) -> Page:
    state.score = state.score + 1
    return index(state)


start_server(State(0))
```

## Student-relevant options

All options other than the state are keyword arguments.

| Option | Type | What it does |
| ------ | ---- | ------------ |
| `initial_state` | any | The starting state, passed to `index` on the first visit and restored on reset. |
| `theme` | `str` | Apply a [theme](themes.md) by name, same effect as `set_website_style(...)`. |
| `site_title` | `str` | The title shown in the browser tab. |
| `favicon` | `str` | The little browser-tab icon: a URL or the path to an image file next to your program. |
| `framed` | `bool` | Whether the app sits inside Drafter's window frame. `set_website_framed(False)` is the usual way to turn this off for [deployment](../your-project/deploy/prepare.md). |
| `in_debug_mode` | `bool` | Whether the debug panel appears. On by default while you develop; `hide_debug_information()` is the usual way to turn it off. |
| `port` | `int` | Which port the local development server listens on, when running from the command line. |
| `host` | `str` | Which network interface the local development server binds. |
| `open_browser` | `bool` | Whether running locally opens a browser tab automatically. |
| `engine` | `str` | Which in-browser Python runs your code; `"pyodide"` is the default and the one these docs cover. |

Several options exist in two forms: a `start_server` keyword and a
configuration function (`set_website_style`, `set_website_title`,
`set_website_framed`, `hide_debug_information`). They do the same
thing; the [configuration functions](site-config.md) read more clearly
and are what the rest of these docs use. Values passed directly to
`start_server` are applied last, so they win if you accidentally use
both.

## Notes

- **Nothing after the call runs.** `start_server` takes over the
  program. Configuration goes before it; there is no "after".
- **Tests run first.** Assertions written above `start_server` execute
  before the site starts, which is why they can stop a broken app
  before anyone sees it.
- **Old v1 options are ignored politely.** Parameters from Drafter v1
  such as `cdn_skulpt` print a warning and do nothing.
- **Command-line flags** can override some of these when you run
  `drafter yourfile.py`; see [Command line](cli.md).

## Related

- [How Drafter works](../start/how-drafter-works.md): why your program
  runs twice and where the server actually lives.
- [Site configuration functions](site-config.md): the `set_` and
  `add_` helpers.
- [Code after start_server never runs](../help/errors/nothing-after-start-server.md).
