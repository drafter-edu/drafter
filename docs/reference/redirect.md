---
page_type: reference
title: Redirect
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Redirect
outcome: Navigate from inside a route.
---

# Redirect

A `Redirect` is a route's way of answering "actually, go run that
other route." Where `return index(state)` builds the other page
*inside* the current request, a `Redirect` makes the browser
properly navigate: the address updates and the back button learns a
new entry.

## Syntax

```python
Redirect("route_name")
Redirect("route_name", new_state)
Redirect("route_name", None, some_parameter="value")
```

| Parameter | Type | Meaning |
| --------- | ---- | ------- |
| `target_route` | `str` | The route to go to, by name. |
| `state_update` | any | Optional new state to apply before redirecting; `None` (the default) leaves state unchanged. |
| `**kwargs` | any | Extra keyword arguments become arguments to the target route, filling its parameters by name. |

## Example

A submit route that does its work, then sends the visitor to a
proper thank-you page whose address they can bookmark and whose back
button behaves:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    signatures: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Petition for More Nap Time"),
        str(len(state.signatures)) + " signatures so far.\n",
        "Your name:",
        TextBox("name"),
        "\n",
        Button("Sign", "sign")
    ])


@route
def sign(state: State, name: str) -> Redirect:
    state.signatures.append(name)
    return Redirect("thanks", state, signer=name)


@route
def thanks(state: State, signer: str) -> Page:
    return Page(state, [
        Header("Thank you, " + signer + "!"),
        "Your dedication to napping is noted.\n",
        Link("Back to the petition", "index")
    ])


start_server(State([]))
```

## Notes

- **When to prefer plain calling**: `return index(state)` is
  simpler and right for most "show the front page again" endings.
  Reach for `Redirect` when the destination should be a real
  navigation: the address bar updates, and pressing back from the
  destination returns *here* rather than skipping it.
- **Kwargs fill parameters**: `Redirect("thanks", state,
  signer=name)` fills `thanks`'s `signer` parameter, the same
  name-matching contract as forms and button arguments.
- **State updates are optional**: pass `None` (or leave the second
  argument off) to redirect without touching state.
- **The target is a route name string**, checked like any button
  target: a name with no matching route produces the
  [unknown route error](../help/errors/route-not-found.md).

## Related

- [Page](page.md) and [Fragment](fragment.md): the rendering
  payloads.
- [Live updates](../concepts/live-updates.md): where redirects fit
  among the payloads.
- [route](route.md): how targets resolve.
