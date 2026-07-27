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

An `Update` is a route's way of changing state while showing nothing:
no new page, no fragment, no visible reaction at all. The page the
visitor sees stays exactly as it is; only the app's memory changes.

## Syntax

```python
Update(new_state)
```

| Parameter | Type | Meaning |
| --------- | ---- | ------- |
| `state_update` | any | The value to store as the current state, replacing what was there. |

## Example

A silent draft-saver: every keystroke stores the text, nothing on
screen reacts, and the Show button proves the state kept up.

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

- **Nothing renders.** If you expected something visible, you wanted
  a [Fragment](fragment.md). `Update` is for bookkeeping: saving
  drafts, recording that something was seen, counting quietly.
- **The whole state is replaced** with the value you pass. The usual
  pattern mutates the existing state and passes it back
  (`state.draft = text` then `Update(state)`), which keeps the type
  stable; handing back a different kind of value causes the
  [state type problem](../help/errors/state-mismatch.md).
- **The visitor cannot tell it happened**, which is the feature and
  the trap. Anything the visitor should notice deserves a fragment
  or a page.
- **In tests**, check the stored value through the payload's
  `state_update` attribute
  (`assert_equal(remember(State(""), "hi").state_update, State("hi"))`),
  or simply call the route on a state you hold and inspect that
  state afterward, since the route mutated it.

## Related

- [Fragment](fragment.md): change part of the page instead.
- [Live updates](../concepts/live-updates.md): the concept.
- [State](../concepts/state.md): what "the current state" means.
