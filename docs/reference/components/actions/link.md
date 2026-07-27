---
page_type: component
title: Link
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - Link
outcome: Navigate by text link, including external URLs.
---

# Link

Group: [Actions](../index.md#actions) · Level: L2

## Description

A `Link` is ordinary clickable text that goes somewhere: another route
in your app, or an external website. Use a `Link` for going places
("About", "Read the rules"); use a [Button](button.md) for doing
things. Like a button, clicking a link to one of your own routes
submits the form fields on the page.

## Syntax

```python
Link(text, url)
Link(text, url, arguments)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `text` | `str` | required | The visible link text. |
| `url` | `str` | required | The name of a target route (`"rules"`), or a full external address (`"https://example.com"`). External addresses are detected automatically. |
| `arguments` | see [Button](button.md) | `None` | Extra values delivered to the target route's parameters. |

Like every component, `Link` also accepts
[styling and attribute keywords](../../keyword-attributes.md).

## Examples

Links between your own pages:

```python drafter height=200
from drafter import *


@route
def index() -> Page:
    return Page([
        "Welcome to the museum.\n",
        Link("Visit the gift shop", "shop")
    ])


@route
def shop() -> Page:
    return Page([
        "Everything is free today.\n",
        Link("Back to the entrance", "index")
    ])


start_server()
```

An external link, which opens the other site instead of running a
route:

```python drafter height=180
from drafter import *


@route
def index() -> Page:
    return Page([
        "Drafter's code lives on ",
        Link("GitHub", "https://github.com/drafter-edu/drafter"),
        ".\n"
    ])


start_server()
```

## Notes

- A link whose `url` names no existing route (and is not a working
  external address) stops the page with a
  [points to non-existent page](../../../help/errors/route-not-found.md)
  error.
- Links render inline with surrounding text and do not force a line
  break; end the previous string with `"\n"` if you want the link on
  its own line.
- External links leave your app; the visitor uses the browser's back
  button to return, and your app's state is still there when they do.

## Accessibility

Link text should say where the link goes ("Visit the gift shop"), not
"here" or "this". Screen-reader users often browse a list of a page's
links out of context.

## Related components

- [Button](button.md): the doing-things counterpart.
- [Argument](argument.md): extra values a link can carry.

## External links

- [The a element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a)
