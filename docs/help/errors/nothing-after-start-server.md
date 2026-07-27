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

There is no error message; that is the confusing part. Code placed
after the `start_server(...)` call, like the last line here, silently
never happens:

```python
from drafter import *


@route
def index() -> Page:
    return Page(["Hello!"])


start_server()
print("Welcome to my site!")  # never printed
```

## What it means

`start_server(...)` does not finish and move on; it hands your whole
program over to Drafter, which runs your routes from then on. The
lines after it would only run if the call returned, and it never
does. This is by design, not a bug.

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
program's two runs and why the call never returns;
[start_server](../../reference/start-server.md) has the full option
list.
