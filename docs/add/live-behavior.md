---
page_type: how-to
title: Add live behavior
level: L3
audience: S
priority: P1
prereqs: [add/pages]
symbols: []
outcome: React to input without a full page change.
---

# Add live behavior

## Goal

You want part of the page to react while the visitor works: a
counter that follows typing, a preview that updates on choosing, a
save that happens silently.

## Before you start

You can build multi-page apps with buttons. Two new pieces combine
here: `on_` event keywords make a component call a route when
something happens, and the route answers with a
[Fragment](../reference/fragment.md) (part of a page),
[Update](../reference/update.md) (state only), or
[Redirect](../reference/redirect.md) (go elsewhere) instead of a
whole `Page`. The concept is
[Live updates](../concepts/live-updates.md).

## Recipe: a live character counter

`on_input` fires on every keystroke; the fragment lands in a named
`Output` region:

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Tweet Composer"),
        "Say it in 50 characters:",
        TextBox("message", "", on_input="count"),
        "\n",
        Output("meter", ["50 characters left"])
    ])


@route
def count(message: str) -> Fragment:
    remaining = 50 - len(message)
    if remaining >= 0:
        report = str(remaining) + " characters left"
    else:
        report = str(-remaining) + " over! Trim it."
    return Fragment([report], target="#meter")


start_server()
```

The event's values arrive by name, exactly like form fields: the
box is named `message`, so the route's `message` parameter gets the
current text.

## Recipe: a silent save

`Update` changes state with no visible reaction, right for
bookkeeping the visitor should not be interrupted by:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    draft: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Autosaving Notepad"),
        TextArea("text", state.draft, rows=4, on_input="autosave"),
        "\n",
        Link("Leave and come back", "elsewhere")
    ])


@route
def autosave(state: State, text: str) -> Update:
    state.draft = text
    return Update(state)


@route
def elsewhere(state: State) -> Page:
    return Page(state, [
        "Off doing something else.\n",
        Link("Back to the notepad", "index")
    ])


start_server(State(""))
```

Leave mid-sentence and come back: the draft survived, because every
keystroke quietly saved it.

## Recipe: redirect after finishing

A submit route that should land somewhere real returns a
`Redirect`, so the address updates and the back button behaves; the
worked example is on the
[Redirect reference page](../reference/redirect.md).

## Choosing among the three

| The route should... | Return |
| ------------------- | ------ |
| Change something visible, in place | `Fragment` |
| Change only what the app remembers | `Update` |
| Move the visitor to another page properly | `Redirect` |
| Rebuild the whole view | `Page`, as always |

## Variations

- Other events: `on_change` (value settled), `on_click`,
  `on_mouseenter`, and friends; the list is on
  [Keywords every component accepts](../reference/keyword-attributes.md).
- Target any component by giving it an `id` and the fragment
  `target="#that_id"`; `Output` is just a convenient pre-named
  region.
- Things that happen on a schedule instead of an action are
  [Timers](timers.md).

## Common problems

- **The fragment replaced the wrong element**: with no `target`, it
  lands in the element that fired the event. Name a target.
- **Typing resets the text box**: the event route returned a `Page`
  (or targeted the box itself); return a fragment aimed at the
  display region only.
- **Other parts of the page went stale**: a fragment redraws only
  its target. If the event changes state that several regions
  display, cover them with the target or use the full-page rhythm.
- **The event never fires**: the keyword must be a supported event
  spelled exactly (`on_input`), and its value must name a real
  route.

## Understand it

[Live updates](../concepts/live-updates.md): why fragments exist
and when to prefer whole pages anyway.

## See another example

The counter in the [Live updates concept](../concepts/live-updates.md),
and the [interactive playground](../examples/playground/interactive.md)
collection.

## Look it up

[Fragment](../reference/fragment.md),
[Update](../reference/update.md),
[Redirect](../reference/redirect.md), and
[Output](../reference/components/input/output.md).

## Fix a problem

[Troubleshooting](../help/troubleshooting.md): the "button does
nothing" entry applies to events too.
