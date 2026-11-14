---
page_type: reference
title: Page
level: L1
audience: S
priority: P0
prereqs: []
symbols:
  - Page
  - PageContent
  - Content
  - Component
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
| `content` | `list` | A list of strings, numbers, booleans, and components, rendered in order. A single string, number, boolean, or component is also accepted, and Drafter wraps it in a list. |

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

A [Picture](data-types/picture.md) value is also allowed as an item.
Drafter shows it as an `Image`.

### A single value without a list

When the content is one string, number, boolean, component, or
`Picture`, the list is optional. `Page("Hello")` builds the same page
as `Page(["Hello"])`, and `Page(state, 5)` builds the same page as
`Page(state, [5])`.

Every other kind of value is an error, whether it is passed alone or
placed inside the list.

| Content | Result |
| ------- | ------ |
| `"Hello"`, `5`, `2.5`, `True` | Accepted, and wrapped in a list. |
| `Button("Go", "index")` | Accepted, and wrapped in a list. |
| A dataclass instance | Error. |
| A dictionary | Error. |
| A tuple | Error. |
| `None` | Error. |
| `["Pets:", ["Ada", "Babbage"]]` (a list inside the list) | Error. |

The error appears when the `Page` is created. In the browser, the
error page is titled `Unusable Value`, and its message names the type
that Drafter found:

```text
The content you returned in this Page was a dict, but it needs to be text, a number, a boolean, a component, or a list of those.
```

For an item inside the list, the message gives the item's position,
counting from zero:

```text
Item number 1 in this Page's content list is a list, but every item needs to be text, a number, a boolean, or a component.
```

To show a value of another type, convert it to text with `str()`
first. To show the items of a list, add them to the content list one
at a time. See
[Page content must be a list](../help/errors/page-content-invalid.md).

### Type names for content

Three names describe content in type annotations. They are useful when
you write a helper function that builds part of a page.

| Name | Meaning |
| ---- | ------- |
| `Component` | The class that every component, such as `Button` or `Header`, is built from. `isinstance(item, Component)` is `True` for a component and `False` for plain text. |
| `Content` | One content item: a component, a string, an `int`, a `float`, or a `bool`. |
| `PageContent` | One content item, or a list of content items. |

```python
def pet_card(name: str, species: str) -> PageContent:
    return Div(bold(name), " the " + species)
```

The result of `pet_card("Ada", "corgi")` is one component, so it can
be placed in a content list like any other item.

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
