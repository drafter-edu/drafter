---
page_type: concept
title: Routes and pages
level: L2
audience: S
priority: P0
prereqs: [start/first-app]
symbols: []
outcome: Explain what a route is and how pages connect.
---

# Routes and pages

## In one sentence

A route is a function that Drafter shows as a page of your site, and your
site is nothing more than routes connected by buttons and links.

## The idea

Marking a function with `#!python @route` registers it as a page. Three
rules govern how that works:

- **The function's name is the page's name.** A route called `menu` is the
  page called `menu`, and it gets a matching web address. You never write
  the address yourself; the name is enough.
- **`index` is the front door.** The route named `index` is your site's
  main page, the one visitors see first. Every Drafter site needs one.
- **A route returns a `Page`.** The `Page` holds a list of content:
  strings, buttons, images, form fields. Whatever the route returns is
  what the visitor sees next.

Pages connect through their content. A `#!python Button("Play", "play")`
or a `#!python Link("About this site", "about")` names the route to go to.
Clicking runs that route, and the `Page` it returns replaces the current
one. That is all navigation is: functions naming other functions.

## See it

A three-page site. Every page can reach the other two, so you can walk in
a circle:

```python drafter height=240
from drafter import *


@route
def index() -> Page:
    return Page([
        "This is the first page.",
        Button("To the second page", "second"),
        Button("To the third page", "third")
    ])


@route
def second() -> Page:
    return Page([
        "This is the second page.",
        Button("To the third page", "third"),
        Button("Back to the start", "index")
    ])


@route
def third() -> Page:
    return Page([
        "This is the third page.",
        Button("Back to the start", "index")
    ])


start_server()
```

These routes take no `state` because this site remembers nothing; a route
only needs the `state` parameter if it uses it. Notice there is no special
"go back" machinery: going back is a button pointing at the page you came
from. The browser's back button also works, and
[State](state.md) explains what it does to your data.

Drafter checks every connection before showing a page. If a button names a
route that does not exist, you get an error saying so, naming the button
and the missing page, instead of a dead button:

```text
Link `Play` points to non-existent page `play`.
```

## What this means for your code

- Name routes the way you would name pages: `menu`, `results`,
  `game_over`. The name appears in the address bar, so make it presentable.
- Every route returns a `Page`; every `Page` content item is in a list,
  even a single string.
- Each button or link names its target route as a string:
  `#!python Button("Play", "play")`.
- If several pages share content (a title, a footer), write a helper
  function that returns those components and call it from each route.
- A route that no button, link, or test reaches is dead code; delete it or
  connect it.

## Where people get confused

- **"Where do I write the URL?"** You do not. The function name is the
  address. `@route` handles the mapping.
- **"Can two routes share a name?"** No. One name, one page. Two functions
  with the same name is also a Python mistake: the second quietly replaces
  the first.
- **"My button does nothing"**: buttons never do nothing; they either
  navigate or show an error. If the page will not display, read the error
  text; it usually names a missing or misspelled route.
- **"Which route runs first?"** `index`, always. The order you define
  routes in the file does not matter to visitors, only to readers of your
  code, so keep `index` first for their sake.

## Go deeper

- [Add and connect pages](../add/pages.md): recipes for linking pages.
- [State](state.md): what travels between your pages.
- [Dynamic pages](dynamic-pages.md): one route that renders many
  different pages.
- [route (reference)](../reference/route.md) and
  [Page (reference)](../reference/page.md): exact behavior and
  parameters.
