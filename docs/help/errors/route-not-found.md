---
page_type: error
title: Link or button points to an unknown route
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix a link or button that points to an unknown route.
error_text: "points to non-existent page"
error_id: request.route_not_found
---

# Link or button points to an unknown route

## The error

```text
Link `Next` points to non-existent page `sumary`.
```

or the same for a `Button`. The friendly version explains that the
link tries to go to a page named `sumary`, but your site has no route
with that name. A closely related message appears when you follow an
address directly: "Drafter could not find the page route your app
tried to open."

## What it means

Before showing a page, Drafter checks that every button and link on
it points at a real route. One of yours names a route that does not
exist, so Drafter stopped the page rather than render it with a
button or link that leads nowhere.

## Where to look

The message names the label and the target. Search your code for that
`Button(...)` or `Link(...)` call, then compare its target string
against your route functions' names.

## Check

Three causes produce this message, and the details in it tell you
which one you have:

- **A typo**: the target almost matches a route name (`"sumary"` vs
  `def summary`). Fix the spelling.
- **A missing decorator**: the function exists, but has no `@route`
  above it, so Drafter never registered it.
- **A route you have not written yet**: you wired the button before
  writing its destination.

## Fix

Make the target string match a decorated route exactly:

```python
@route
def summary(state: State) -> Page:
    ...

# In the page that links there:
Button("Next", "summary")
```

## Confirm

Reload and click the fixed control; the target page should render.
If you have tests, add
`assert_has(index(state), Button("Next", "summary"))` so the
connection stays checked.

## Prevent

Name routes with plain, short, lowercase names you can spell
confidently, and write the destination route (even as a stub
returning a bare page) before wiring buttons to it.

## Understand

[Routes and pages](../../concepts/routes-and-pages.md) explains how
route names become addresses and how Drafter verifies connections;
[Add and connect pages](../../add/pages.md) is the how-to.
