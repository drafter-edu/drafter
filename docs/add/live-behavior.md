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
counter that follows their typing, a preview that updates when they
pick an option, or a save that happens silently in the background.

## Before you start

You can build multi-page apps with buttons. This page combines two
new pieces. First, `on_` event keywords make a component call a
route when something happens. Second, that route responds with a
[Fragment](../reference/fragment.md) (a piece of a page), an
[Update](../reference/update.md) (a change to state only), or a
[Redirect](../reference/redirect.md) (an instruction to go to
another page) instead of a whole `Page`. The concept behind both is
explained in [Live updates](../concepts/live-updates.md).

## Recipe: a live character counter

`on_input` fires on every keystroke, and the fragment it triggers
is placed into a named `Output` region:

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

`Update` changes state without any visible reaction, which makes it
the right choice for bookkeeping that should not interrupt the
visitor:

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

Try leaving mid-sentence and coming back: the draft is still there,
because every keystroke saved it.

## Recipe: redirect after finishing

When a submit route should leave the visitor on an actual page,
return a `Redirect`. The browser's address updates, and the back
button works as expected. A worked example is on the
[Redirect reference page](../reference/redirect.md).

## Choosing among the three

| The route should... | Return |
| ------------------- | ------ |
| Change something visible, in place | `Fragment` |
| Change only what the app remembers | `Update` |
| Move the visitor to another page properly | `Redirect` |
| Rebuild the whole view | `Page`, as always |

## Variations

- Other events exist, including `on_change` (fires when the value
  settles), `on_click`, and `on_mouseenter`; the full list is on
  [Keywords every component accepts](../reference/keyword-attributes.md).
- You can target any component by giving it an `id` and giving the
  fragment `target="#that_id"`; `Output` is a convenient pre-named
  region.
- For behavior that happens on a schedule instead of in response to
  an action, see [Timers](timers.md).

## Common problems

- **The fragment replaced the wrong element**: with no `target`, it
  lands in the element that fired the event. Name a target.
- **Typing resets the text box**: the event route returned a `Page`
  (or targeted the box itself); return a fragment aimed at the
  display region only.
- **Other parts of the page went stale**: a fragment redraws only
  its target. If the event changes state that several regions
  display, choose a target that covers all of them, or return a
  whole `Page` instead.
- **The event never fires**: the keyword must be a supported event
  spelled exactly (`on_input`), and its value must name a real
  route.

## Understand it

[Live updates](../concepts/live-updates.md) explains why fragments
exist and when a whole page is still the better choice.

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
