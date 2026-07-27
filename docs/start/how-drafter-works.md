---
page_type: concept
title: How Drafter works
level: L1
audience: S
priority: P0
prereqs: [start/debug-panel]
symbols: []
outcome: Hold a correct minimal model of where and when your program runs.
---

# How Drafter works

## In one sentence

Your Python program runs **inside the browser**: there is no separate
server computer, your routes are functions the browser calls to build each
page, and your state lives in the browser's memory until the page is
closed or reloaded.

## The idea

When you run a Drafter program, it actually runs twice:

1. **Once on your computer**, from top to bottom, like any Python file.
   This run defines your `State`, registers your routes, and runs your
   `assert_` tests. When it reaches `start_server(...)`, it hands
   everything over to the site. That is why code written after
   `start_server(...)` never runs.
2. **Again inside the browser**, where the real app lives. The browser
   can run Python directly, so your routes execute right there: every
   button click calls one of your functions, which returns the next
   `Page` to display.

There is no backend. Nothing is sent to a server when a button is clicked;
no other computer is involved. This has three consequences worth
memorizing:

- **State is temporary.** It lives in the browser's memory. Reloading the
  page restarts the app from its initial state. For a course project, that
  is normally fine, and it means you never have to clean up a database.
  Databases bring plenty of complexity of their own, so it is better to
  hold off on them until you actually need one.
- **Each visitor gets their own app.** If two people open your site, they
  each get an independent copy with independent state. They cannot see
  each other's clicks.
- **Nothing is secret.** Your entire program is delivered to the visitor's
  browser. Anyone can read your code, so never put a password or a secret
  in it, and never treat a login page as real security.

## See it

The two runs are visible in a single program. The `assert_` test runs in
run one, before the site exists; the route runs in run two, every time the
page is shown:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    visits: int


@route
def index(state: State) -> Page:
    state.visits = state.visits + 1
    return Page(state, [
        "This page has been built " + str(state.visits) + " times.\n",
        Button("Build it again", "index")
    ])


assert_state(index(State(0)), State(1))

start_server(State(0))
```

Click the button a few times, then reload your browser tab on your own
computer and watch the count start over. The count resets because state
lives only in memory.

## What this means for your code

- Put `start_server(...)` last; nothing after it runs.
- Put tests before `start_server(...)`; they run at startup, every time.
- Design your `State` to hold everything the app needs to remember, and
  expect it to reset on reload.
- Do not store secrets, passwords, or private data in your program.
- Your routes must be complete functions: everything a page needs comes
  in through `state` and parameters, and comes out in the returned `Page`.

## Where people get confused

- **"My app saves things, right?"** No. State is held in memory, not
  saved to storage, so closing or reloading the tab resets it. You will
  eventually learn how to save values to *local storage* in the browser,
  but that comes much later.
- **"The server crashed"**: there is no server. If the app breaks, the
  cause is in your program, and the error message on the page plus the
  debug panel will point to it.
- **"Two players can share the score"**: each browser tab runs its own
  independent copy of the app. Multiplayer needs a real backend, which is
  [beyond Drafter](../extend/security.md).

## Go deeper

- [State](../concepts/state.md) covers designing what your app
  remembers.
- [Routes and pages](../concepts/routes-and-pages.md) explains how
  pages connect.
- [Python in the browser](../extend/pyodide.md) describes how the
  browser runs Python at all, and what its limits are.
- [Security honestly](../extend/security.md) spells out exactly what is
  and is not protected.

<div class="grid cards" markdown>

- **Next: Guided Projects**

    ---

    You know the pieces. The guided projects help you build something
    worth showing, starting with a virtual pet.

    [Go to Guided Projects](../tutorials/index.md)

</div>
