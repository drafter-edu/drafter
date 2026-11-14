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

| Option | Type | Default | What it does |
| ------ | ---- | ------- | ------------ |
| `initial_state` | any | `None` | The starting state, passed to `index` on the first visit and restored by the built-in [`--reset`](route.md#built-in-routes) route. |
| `theme` | `str` | `"default"` | Apply a [theme](themes.md) by name, same effect as `set_website_style(...)`. |
| `site_title` | `str` | `"Drafter Application"` | The title shown in the browser tab. |
| `favicon` | `str` | Drafter's own icon | The small browser-tab icon: a URL or the path to an image file next to your program. |
| `framed` | `bool` | `True` | Whether the app sits inside Drafter's window frame. `set_website_framed(False)` is the usual way to turn this off for [deployment](../your-project/deploy/prepare.md). |
| `in_debug_mode` | `bool` | `True` | Whether the debug panel appears. `False` shows the site the way visitors will see it, which is the same as the `--production` flag. `hide_debug_information()` is the usual way to turn the panel off. |
| `console_mode` | `str` | `"auto"` | Where `print()` output appears in the browser. `"auto"` shows a console in the page footer while the debug panel is on. `"hover"` shows a floating console box, which also appears when the debug panel is off. `"toast"` shows each line briefly in a corner, and `"devtools"` sends output only to the browser's developer console. |
| `port` | `int` | `8000` | Which port the local development server listens on. The default port moves to the next free one when it is busy. A port you choose is never moved. |
| `host` | `str` | `"localhost"` | Which network interface the local development server binds. |
| `open_browser` | `bool` | `True` | Whether running locally opens a browser tab automatically. |
| `browser` | `str` | `None` | Which browser opens the tab: `"chrome"`, `"firefox"`, `"safari"`, `"edge"`, or `"default"` for your computer's usual browser. When this is not set, Drafter uses Chrome if installed, then Firefox, then the default. |
| `engine` | `str` | `"pyodide"` | Which in-browser Python runs your code. `"pyodide"` is the one these docs cover. |
| `use_reloader` | `bool` | `True` | Whether saving a file restarts the site automatically. [Live reload](live-reload.md) covers this and the finer-grained `watch_...` options. |
| `skip` | `bool` | `False` | Do nothing at all: no server, no compilation. Meant for test runners; see the note below. |

Several options exist in two forms: a `start_server` keyword and a
configuration function (`set_website_style`, `set_website_title`,
`set_website_framed`, `hide_debug_information`). The
[configuration functions](site-config.md) read more clearly and are
what the rest of these docs use.

Set each option in only one of the two forms. When a configuration
function and a `start_server` keyword give different values for the
same option, the result is not dependable. For example, the browser
tab shows the title from `set_website_title`, while the theme follows
the `start_server` keyword.

!!! warning "A misspelled option is ignored without any message"

    `start_server` accepts any keyword. A keyword that it does not
    recognize, such as `sight_title` in place of `site_title`, produces
    no error and no warning, and the real option keeps its default. If
    an option seems to have no effect, check its spelling against the
    table above.

## Where settings come from

A setting can be given in three places. The examples all set the
theme.

1. **A `start_server` keyword.** The setting is part of your program,
   so it is still in effect when the site is deployed.

    ```python
    start_server(State(0), theme="terminal")
    ```

2. **A command line flag.** The setting applies to one run.
   [Command line](cli.md) lists the flags.

    ```console
    drafter my_app.py --theme terminal
    ```

3. **An environment variable.** The variable's name is `DRAFTER_`
   followed by the setting's name in capital letters.

    ```console
    DRAFTER_THEME=terminal python my_app.py
    ```

    That line is written for macOS, Linux, and Git Bash. In Windows
    PowerShell, set the variable on its own line first with
    `$env:DRAFTER_THEME = "terminal"`, and then run the program.

When the same setting is given in more than one place, a
`start_server` keyword wins over a flag, and a flag wins over an
environment variable.

The environment variables for `port`, `host`, `open_browser`, and
`use_reloader` currently have no effect. Use the keyword or the flag
for those four settings.

## Notes

- **Nothing after the call runs.** `start_server` takes over the
  program, so all configuration must come before it; code placed
  after the call never executes.
- **Tests run first.** Assertions written above `start_server` execute
  before the site starts. A failing assertion prints a FAILURE message
  and the site still starts. See
  [Testing functions](testing-functions.md).
- **Skipping the server for tests.** Setting the `DRAFTER_SKIP`
  environment variable (or passing `skip=True`, or running with the
  `--skip` flag) makes `start_server` return immediately without
  starting the server or compiling anything, so a unit test runner
  can import your file without launching the site.
- **Watching a large folder.** If your program sits in a broad folder
  like Downloads or your home directory, Drafter prints a notice and
  watches only your program and the files your site uses, instead of
  the entire folder. [Live reload](live-reload.md) has the details.
- **Old v1 options are ignored.** Parameters from Drafter v1 such as
  `cdn_skulpt` print a warning and do nothing.
- **Command-line flags** set many of the same options for one run of
  `drafter yourfile.py`. A keyword in `start_server` wins when both
  are given. See [Command line](cli.md) and
  [Where settings come from](#where-settings-come-from).

## Related

- [How Drafter works](../start/how-drafter-works.md): why your program
  runs twice and where the server actually lives.
- [Site configuration functions](site-config.md): the `set_` and
  `add_` helpers.
- [Code after start_server never runs](../help/errors/nothing-after-start-server.md).
