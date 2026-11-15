---
page_type: error
title: Code after start_server() never runs
level: L1
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Understand why code after start_server() never runs.
error_text: "code after start_server() never runs"
---

# Code after start_server() never runs

## The error

There is no error page. Code placed after the `start_server(...)`
call, like the last line here, does not run when you expect it to:

```python
from drafter import *


@route
def index() -> Page:
    return Page(["Hello!"])


start_server()
print("Welcome to my site!")  # not printed while the site is running
```

The terminal (the Thonny shell) does not show "Welcome to my site!"
for as long as the site runs. When the program starts, Drafter prints
a warning there that names the file and the line:

```text
Warning: main.py has code after start_server(...), starting on line 10. That code will not run until the server stops. Make start_server(...) the last line of your file.
```

In the browser, the debug panel lists the same problem as a warning:

```text
Line 10 of main.py comes after start_server(...). That code does not run
when you would expect: on your computer it waits until the server stops,
and in the browser it runs right after the first page appears.
```

The site still starts. The warning is about statements, so comments
and blank lines after the call do not cause it.

## What it means

Your program runs twice, once on your computer and once in the
browser. On your computer, `start_server(...)` starts the site and
does not finish until the server stops, so the lines after it wait
until then. In the browser, the call finishes once the first page is
ready, and the lines after it run one time, right after the first page
appears. The `print` in this example therefore appears in the Console
box in the footer of the browser page as the site loads, and in the
terminal only after the server stops. Code that runs at a
different moment in each place is hard to reason about, which is why
nothing should follow the call.

## Where to look

The warning names the line where the extra code starts. Look at that
line and everything below it, at the bottom of your file after the
`start_server(...)` call.

## Check

What was the code after the call trying to do?

- **Set something up** (configuration, initial data): it belongs
  before the call.
- **React to the visitor** (print when clicked, change state): it
  belongs inside a route.
- **Run tests**: assertions go before the call; they run at startup
  and report to the debug panel.

## Fix

Move the code where it belongs: configuration and tests go before
the call, and behavior goes inside routes.

```python
from drafter import *

set_website_title("My Site")


@route
def index() -> Page:
    print("Someone visited the front page!")
    return Page(["Hello!"])


start_server()
```

## Confirm

Run the program again. The warning is gone from the terminal and from
the debug panel, and the moved code visibly happens: the configuration
takes effect, the print appears (in the console; see
[Print and the console](../printing-and-console.md)) when the route
runs.

## Prevent

Keep `start_server(...)` as the last line of the file, always, and
treat "where does this line go?" as a two-answer question: before the
call, or inside a route.

## Understand

[How Drafter works](../../start/how-drafter-works.md) explains the
program's two runs, and
[start_server](../../reference/start-server.md) has the full option
list.
