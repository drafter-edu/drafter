---
page_type: reference
title: Page
level: L1
audience: S
priority: P0
prereqs: []
symbols:
  - Page
outcome: Know exact Page behavior.
---

# Page

A `Page` is the value a route returns: the new state plus a list of
everything to show. Drafter renders the list top to bottom, replacing
whatever page was on screen before.

## Syntax

```python
Page(state, content)
Page(content)
```

| Parameter | Type | Meaning |
| --------- | ---- | ------- |
| `state` | any | The state to carry forward, almost always your `State` dataclass. When you pass only one argument, the state is `None`. |
| `content` | `list` | A list of strings, numbers, booleans, and components, rendered in order. Must be a list, even for a single item. |

Two more parameters, `css` and `js`, accept raw CSS and JavaScript to
inject when the page renders. They are for advanced use; see
[JavaScript interop](../extend/javascript.md).

## With state and without

An app with a `State` dataclass passes it as the first argument, so the
next route receives the current values:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    visits: int


@route
def index(state: State) -> Page:
    state.visits = state.visits + 1
    return Page(state, [
        "Visits so far: " + str(state.visits) + "\n",
        Button("Visit again", "index")
    ])


start_server(State(0))
```

An app with nothing to remember can skip state entirely:

```python drafter height=200
from drafter import *


@route
def index() -> Page:
    return Page([
        "This site remembers nothing.\n",
        Link("See for yourself", "again")
    ])


@route
def again() -> Page:
    return Page([
        "Still nothing remembered.\n",
        Link("Back", "index")
    ])


start_server()
```

## What content can hold

Each item in the content list is a string, a number, a boolean, or a
component:

- **Strings** render as text. Drafter does not add line breaks between
  items; end a string with `"\n"` where you want the next item to start
  on a new line.
- **Numbers and booleans** (`int`, `float`, `bool`) render as their
  text form, so `state.score` works directly without `str()`.
- **Components** (`Button`, `TextBox`, `Header`, `Image`, and the rest
  of the [component list](components/index.md)) render as their HTML.

A single string, value, or component is quietly wrapped in a list for
you, but anything else (a dataclass, a dictionary, a list of lists)
produces a friendly error that names the route that returned it. See
[Page content must be a list](../help/errors/page-content-invalid.md).

## What Drafter verifies

Before showing a page, Drafter checks it:

- **Links and buttons must point somewhere real.** A `Button` or `Link`
  whose target names no existing route stops the page with a
  [points to non-existent page](../help/errors/route-not-found.md)
  error, rather than rendering a dead control.
- **Input names should be unique.** Two form components with the same
  `name` on one page would both try to fill the same parameter; see
  [Two components share a name](../help/errors/duplicate-component-name.md).

## Notes

- A route builds a fresh `Page` every time it runs. Pages are
  descriptions of a screen, not the screen itself; returning the same
  `Page` twice renders the same thing twice.
- Routes can call other routes that return a `Page`. Ending a route
  with `return index(state)` is the standard way to show the front page
  after making a change.
- In tests, compare pages directly:
  `assert_has(index(State(0)), Button("Visit again", "index"))`. See
  [Test a feature](../add/test-a-feature.md).

## Related

- [route](route.md): how a function comes to return pages.
- [Fragment](fragment.md), [Update](update.md),
  [Redirect](redirect.md): the other values a route can return.
- [Routes and pages](../concepts/routes-and-pages.md): the concept
  behind the machinery.
