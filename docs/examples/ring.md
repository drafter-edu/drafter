---
page_type: example
title: Three linked pages
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: See stateless multi-page navigation.
---

# Three linked pages

## What it does

This example joins three pages in a ring: the first links to the
second, the second links to the third, and the third links back to
the first. There is no state at all, so the example shows nothing
but navigation. It is the smallest app that has more than one page.

## Try it

Walk the ring and end up back where you started.

```python drafter height=200
from drafter import *


@route
def index() -> Page:
    return Page([
        "Welcome to the trailhead.\n",
        Link("Hike to the waterfall", "waterfall")
    ])


@route
def waterfall() -> Page:
    return Page([
        "The waterfall roars.\n",
        Link("Continue to the summit", "summit")
    ])


@route
def summit() -> Page:
    return Page([
        "The summit! You can see your house from here.\n",
        Link("Head back down", "index")
    ])


assert_has(index(), Link("Hike to the waterfall", "waterfall"))
assert_has(waterfall(), Link("Continue to the summit", "summit"))
assert_has(summit(), Link("Head back down", "index"))

start_server()
```

## The code

Each page comes from its own route: a function marked with `@route`
that returns a `Page`. Because there is nothing to remember, the
routes take no parameters and each `Page` receives only a content
list. Every page contains exactly one `Link`, and each link's target
names the next route as a string: `"waterfall"`, `"summit"`,
`"index"`.

## How it works

A `Link`'s target is a route name. When the visitor clicks "Hike to
the waterfall", Drafter runs the route named `waterfall` and shows the
page it returns. The ring closes because the last page targets
`"index"`, the special route every app starts from.

Before showing any page, Drafter verifies its links point at real
routes, so a typo in a target is caught immediately rather than
becoming a dead link a visitor finds later.

## Make it yours

1. **Modify**: rewrite the trail with three stops of your own,
   described in your own words.
2. **Modify**: swap the `Link`s for `Button`s. When does each feel
   right?
3. **Complete**: add a fourth stop between the waterfall and the
   summit without breaking the ring.
4. **Combine**: give every page a second link jumping straight home,
   using a shared helper function (see
   [Add and connect pages](../add/pages.md)).
5. **Create**: turn the ring into a fork: the trailhead offers two
   paths that reunite at the summit.

## Tests

There is one `assert_has` per page, checking that each page offers
the link to the next stop; those links are what make the ring a
ring. If a change breaks the chain, the failing test identifies
which page is missing its link.

## Likely errors

- **A misspelled target**, such as `Link("...", "sumit")`, stops the
  page with a
  [points to non-existent page](../help/errors/route-not-found.md)
  error.
- **Forgetting `@route`** on a function makes its name invalid as a
  target; the same error points at every link that mentions it.
- **Two routes with the same name**: Python keeps only the second
  function, so one page of your ring disappears without any warning.

## Related

- [Add and connect pages](../add/pages.md) is the how-to guide,
  covering shared headers and making sure every page has a way back.
- [Routes and pages](../concepts/routes-and-pages.md) explains what
  a route is.
- [Link](../reference/components/actions/link.md) and
  [Button](../reference/components/actions/button.md) are the two
  components that connect pages.
