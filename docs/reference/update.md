---
page_type: reference
title: Update
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Update
outcome: Know how state-only responses work.
---

# Update

Returning an `Update` changes the state without showing anything new:
no page, no fragment, and no visible reaction at all. The page the
visitor sees stays exactly as it is; only the stored state changes.

## Syntax

```python
Update(new_state)
```

| Parameter | Type | Meaning |
| --------- | ---- | ------- |
| `state_update` | any | The value to store as the current state, replacing what was there. |

## Example

This example saves a draft silently. Every keystroke stores the
current text without changing anything on screen, and the
**Show what was saved** button displays the stored draft to confirm
that the state kept up.

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    draft: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Quiet Notebook"),
        "Write; the app remembers without reacting:",
        TextBox("text", state.draft, on_input="remember"),
        "\n",
        Button("Show what was saved", "reveal")
    ])


@route
def remember(state: State, text: str) -> Update:
    state.draft = text
    return Update(state)


@route
def reveal(state: State) -> Page:
    return Page(state, [
        "The saved draft: " + state.draft + "\n",
        Link("Back", "index")
    ])


start_server(State(""))
```

## Notes

- **Nothing renders.** If you expected something visible to change,
  use a [Fragment](fragment.md) instead. `Update` is for bookkeeping
  tasks such as saving drafts, recording that something was seen, or
  counting events without displaying them.
- **The whole state is replaced** with the value you pass. The usual
  pattern mutates the existing state and passes it back
  (`state.draft = text` then `Update(state)`), which keeps the type
  stable; handing back a different kind of value causes the
  [state type problem](../help/errors/state-mismatch.md).
- **The visitor cannot tell that anything happened.** That is the
  point of `Update`, but it can also be a trap: if the visitor
  should notice a change, return a fragment or a page instead.
- **In tests**, check the stored value through the payload's
  `state_update` attribute
  (`assert_equal(remember(State(""), "hi").state_update, State("hi"))`),
  or call the route on a state you hold and inspect that state
  afterward, since the route mutated it.

## Related

- [Fragment](fragment.md): change part of the page instead.
- [Live updates](../concepts/live-updates.md): the concept behind
  state-only responses.
- [State](../concepts/state.md): what "the current state" means.
