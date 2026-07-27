---
page_type: how-to
title: Add and connect pages
level: L2
audience: S
priority: P0
prereqs: [start/first-app]
symbols: []
outcome: Create and link several pages.
---

# Add and connect pages

## Goal

You want your app to have more than one page, with ways to move between
them.

## Before you start

You can build a one-page app with a button. When you finish this page,
your app will have several pages that link to each other, share a common
header, and always offer a way back.

## The smallest version

A new page is a new route: a function with `@route` that returns a
`Page`. Connect pages with `Button` (an action to click) or `Link` (an
ordinary text link). Both name their target route as a string:

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        "Welcome to the arcade.\n",
        Button("Play a game", "game"),
        Link("Read the rules", "rules")
    ])


@route
def game() -> Page:
    return Page([
        "The game happens here.\n",
        Button("Back to the front", "index")
    ])


@route
def rules() -> Page:
    return Page([
        "Rule 1: have fun.\n",
        Link("Back to the front", "index")
    ])


start_server()
```

When to use which: a `Button` looks like an action and is best for doing
things ("Play", "Submit", "Feed"); a `Link` looks like text and is best
for going places ("Read the rules", "About"). Either can point to any
route.

## Recipe: a shared header on every page

When several pages repeat the same top content, write a helper function
that returns the shared components, and start each page's list with it.
A list plus a list glues them together:

```python drafter height=300
from drafter import *


def header(title: str) -> list:
    return [
        Header(title),
        Link("Home", "index"),
        " | ",
        Link("About", "about"),
        "\n"
    ]


@route
def index() -> Page:
    return Page(header("My Arcade") + [
        "Pick a destination above."
    ])


@route
def about() -> Page:
    return Page(header("About") + [
        "Built with Drafter."
    ])


start_server()
```

Change the header helper once, and every page changes. This is the same
helper-function habit from the
[virtual pet's mood](../tutorials/virtual-pet.md), applied to content.

## Recipe: always offer a way back

Every page a visitor can reach should have a button or link leading
somewhere, usually back to `index`. A page with no way out forces the
browser's back button, which works but feels like a dead end. Walk your
own app: from `index`, can you reach every page and return without
touching the browser controls?

## Common problems

- **A "points to non-existent page" error**: a button or link names a
  route that does not exist. Check the spelling against the function
  name, and make sure the function has `@route`.
- **You wrote a route but cannot see it**: nothing links to it yet. A
  route becomes reachable when some page names it, or when you visit its
  address directly.
- **Two functions with the same name**: Python keeps only the second one,
  silently. Every route needs its own name.
- **Your pages have state but the new one errors**: if your app has a
  `State`, every route that page connects to should take `state` as its
  first parameter and pass it along in `Page(state, [...])`.

## Understand it

[Routes and pages](../concepts/routes-and-pages.md): what a route is, how
names become addresses, and how Drafter verifies connections.

## See another example

[Three linked pages](../examples/ring.md): a minimal ring of pages you
can walk in a circle.

## Look it up

[route](../reference/route.md),
[Page](../reference/page.md),
[Button](../reference/components/actions/button.md), and
[Link](../reference/components/actions/link.md).

## Fix a problem

[Link or button points to an unknown route](../help/errors/route-not-found.md).
