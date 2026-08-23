---
page_type: component
title: Details
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - Details
outcome: Make collapsible sections and accordions.
---

# Details

Group: [Layout](../index.md#layout)

## Description

A `Details` is a collapsible section: an always-visible summary
line the visitor clicks to reveal (or hide) the content inside.
The browser handles the opening and closing itself, with no
routes or state involved. Use it for hints, spoilers, optional
explanations, and anything long that most visitors will not need.

## Syntax

```python
Details(summary, content)
Details(summary, content, more_content, open=True)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `summary` | string or component | required | The always-visible clickable line. |
| `*content` | strings, numbers, booleans, or components | required | What reveals when opened. |
| `open` | `bool` | `False` | Start expanded instead of collapsed. |
| `group` | `str` | none | Name relating several `Details`; within a group, opening one closes the others (an accordion). |

## Examples

Three hints that reveal one at a time, because they share a
group:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Riddle"),
        "What has four legs, ignores you, and owns your house?\n",
        Details("Hint 1", "It is smaller than a dog.",
                group="hints"),
        Details("Hint 2", "It is currently on your keyboard.",
                group="hints"),
        Details("The answer", "A cat. Specifically, Captain.",
                group="hints")
    ])


start_server(State())
```

## Notes

- Opening and closing happens entirely in the browser; your
  routes never hear about it, and the open/closed position is
  not part of your state.
- Because a re-render rebuilds the page, sections snap back to
  their `open` argument whenever a route returns a new `Page`.
  Keep that in mind on pages with frequent updates.
- Tests see all the content, open or closed;
  `assert_has(page, "A cat. Specifically, Captain.")` passes
  regardless.

## Related components

- [Div (Box)](div.md): grouping without the collapse behavior.
- [Row](row.md): side-by-side arrangement.

## External links

- [The details element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/details)
