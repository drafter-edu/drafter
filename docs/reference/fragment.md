---
page_type: reference
title: Fragment
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Fragment
outcome: Know how partial page updates work.
---

# Fragment

A route returns a `Fragment` to replace one part of the current page
instead of returning a whole new [Page](page.md). Fragments are the
main tool for [live updates](../concepts/live-updates.md), such as
character counters, previews, and anything else that changes while
the visitor works.

## Syntax

```python
Fragment(state, content)
Fragment(state, content, target="#some_id")
Fragment(content)
```

| Parameter | Type | Meaning |
| --------- | ---- | ------- |
| `state` | any | The state to carry forward, exactly as in `Page`. With one argument, the state is `None`. |
| `content` | `list` | Strings and components, same rules as [Page content](page.md#what-content-can-hold). |
| `target` | `str` or `None` | Where the content is placed. A CSS-style selector such as `"#counter"` (an element with `id="counter"`) or `".score"` (elements with that class). `None`, the default, targets the element that triggered the request. |
| `css`, `js` | `str` | Advanced: raw CSS/JavaScript to inject with the fragment. |

## Example

This example shows the most common pattern: an event route updates a
named region while the rest of the page stays the same.

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Shouting Machine"),
        "Type something to shout:",
        TextBox("words", "", on_input="shout"),
        "\n",
        Output("display", ["..."])
    ])


@route
def shout(words: str) -> Fragment:
    return Fragment([words.upper() + "!"], target="#display")


start_server()
```

## Notes

- **A `Page` is a `Fragment`** whose target is the whole page body,
  so everything true of page content is also true of fragment
  content.
- **`target=None` targets the element the event came from.** That
  default is useful for a button that replaces itself, but it can be
  surprising anywhere else. When in doubt, name a target explicitly.
- **Give fragments a place to land**: an
  [Output](components/input/output.md) region (`Output("display",
  ...)` has id `display`) or any component with an `id` keyword.
- **State flows as usual.** A fragment's `state` becomes the current
  state, exactly like a page's. A stateless fragment
  (`Fragment([...])`) carries `None`, which is only safe in a
  stateless app; in a stateful app, pass the state through.
- **Only the target redraws.** If other parts of the page display
  state that the fragment just changed, they stay out of date until
  the next full page. Target a region that covers everything
  affected, or return a `Page` instead.
- **In tests**, routes returning fragments are called like any
  other: `assert_has(shout("hi"), "HI!")`.

## Related

- [Live updates](../concepts/live-updates.md): the concept behind
  fragments.
- [Add live behavior](../add/live-behavior.md): recipes for common
  live-update patterns.
- [Update](update.md): change the state without sending any content
  at all.
- [Redirect](redirect.md): send the visitor to a different route
  instead.
