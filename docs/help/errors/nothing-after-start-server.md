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

There is no error page, no title, and no message, which is the
confusing part. Code placed after the `start_server(...)` call, like
the last line here, does not run where you expect it to:

```python
from drafter import *


@route
def index() -> Page:
    return Page(["Hello!"])


start_server()
print("Welcome to my site!")  # never printed in the terminal
```

The terminal (the Thonny shell) never shows "Welcome to my site!",
no matter how long the site runs.

## What it means

Your program runs twice, once on your computer and once in the
browser. On your computer, `start_server(...)` starts the site and
keeps running for as long as the site is up, so Python does not reach
the lines after it. In the browser, the call finishes once the first
page is ready, and the lines after it run one time as the site loads.
The `print` in this example therefore appears in the Console box in
the footer of the browser page and never in the terminal. Code that
runs in one place and not the other is hard to reason about, which is
why nothing should follow the call.

## Where to look

Look at the bottom of your file, at anything after the
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

The moved code visibly happens: the configuration takes effect, the
print appears (in the console; see
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
