---
page_type: how-to
title: JavaScript interop
level: L4
audience: S
priority: P2
prereqs: [extend/pyodide]
symbols: []
outcome: Call JavaScript when Python is not enough.
---

# JavaScript interop

## Goal

Reach the browser's own capabilities (the page, its elements,
web APIs) from your Python code, for the rare feature no
component covers.

## Before you start

You have read [Python in the browser](pyodide.md): your routes
run inside the browser, which is what makes this possible at
all. Fair warning that this page leaves the paved road; the
techniques here are real but sharp-edged, and most projects that
think they need them actually need a
[component](../reference/components/index.md) they have not met
yet.

## The `js` module

Inside Pyodide, `import js` exposes the browser's JavaScript
world as Python objects. `js.document` is the page,
`js.window` the browser window, and calls translate naturally:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Browser Inspector"),
        Button("Inspect my browser", "inspect"),
        "\n" + state.report
    ])


@route
def inspect(state: State) -> Page:
    import js
    state.report = ("Your window is "
                    + str(js.window.innerWidth) + " by "
                    + str(js.window.innerHeight)
                    + " pixels, and your browser calls itself: "
                    + str(js.navigator.userAgent)[:60] + "...")
    return index(state)


start_server(State(""))
```

Keep the import inside the route: routes only run in the
browser, while the top of your file also runs in normal Python,
where `js` does not exist.

## Recipe: touching the live page

`js.document` finds and changes elements directly. The
[Canvas](../reference/components/media/canvas.md) page is a
complete worked example: find the element by id, draw on it,
and return an `Update` so the re-render does not erase the work.
The same shape (find, mutate, `Update`) fits scrolling to an
element, focusing a field, or reading a measurement.

## Recipe: shipping JavaScript with a page

`Page` accepts `js` and `css` arguments carrying code to run and
styles to apply when that page renders:

```python
@route
def fancy(state: State) -> Page:
    return Page(state, [
        Header("Confetti Zone"),
    ], js="console.log('The confetti zone was entered.')")
```

This is the door for small snippets copied from tutorials.
Site-wide equivalents exist as
[command-line flags](../reference/cli.md)
(`--additional-js-content` and friends).

## Custom elements exist

Drafter's own interactive components (Timer, Map, Camera) are
custom HTML elements written in TypeScript, paired with Python
classes that declare their events. Building one is a real
library contribution rather than an app technique;
[Build your own components](custom-components.md) shows the
in-Python levels first and points into the
[developer docs](../dev/index.md) for the full path.

## Common problems

- **`ModuleNotFoundError: js` during startup**: the import ran
  on your computer. Move it inside a route.
- **The change vanished immediately**: your event route returned
  a `Page`, and the re-render rebuilt the element you mutated.
  Return `Update(state)` when you changed the page by hand.
- **Working with `js` values feels odd**: they are JavaScript
  objects wearing Python clothes; convert with `str()`, `int()`,
  or `list()` at the border rather than passing them deep into
  your program (or storing them in state, where they do not
  belong).
- **A copied snippet needs a library from a CDN**: script tags
  can be injected with the CLI flags above, but network-loaded
  libraries complicate deployment and can disappear; prefer
  staying inside Drafter's toolkit.

## Related

- [Python in the browser](pyodide.md): why this works.
- [Canvas](../reference/components/media/canvas.md): the worked
  example.
- [Pyodide's guide to the js module](https://pyodide.org/en/stable/usage/type-conversions.html)
