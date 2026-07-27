---
page_type: component
title: RemovePersistent
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - RemovePersistent
outcome: Evict a persistent component.
---

# RemovePersistent

Group: [Time](../index.md#time)

## Description

`RemovePersistent` ends a persistent component: the background
music, the game clock, or the live map that `persistent=True`
kept running across page changes. Place it in the page where the
persistence should stop; it renders nothing visible, and when
that page loads, the matching component is stopped and
discarded.

## Syntax

```python
RemovePersistent(target_id)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `target` | `str` or a component | required | Which persistent component to remove: the `id` you gave it (the reliable way), or an equivalent component built with the same arguments. |

## Examples

Background music that plays through the whole game and stops on
the game-over page:

```python
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Corgi Quest"),
        Audio("theme.mp3", autoplay=True, loop=True,
              persistent=True, id="theme-music"),
        Button("Play a round", "play")
    ])


@route
def play(state: State) -> Page:
    state.score = state.score + 10
    if state.score >= 30:
        return game_over(state)
    return Page(state, [
        "Score: " + str(state.score) + "\n",
        Button("Keep going", "play")
    ])


@route
def game_over(state: State) -> Page:
    return Page(state, [
        Header("Quest complete!"),
        RemovePersistent("theme-music")
    ])


start_server(State(0))
```

(Shown as a listing because it needs a `theme.mp3` next to the
program.)

## Notes

- Give persistent components an explicit `id` at creation, as
  above; removing by id is unambiguous. Passing an equivalent
  component works only when its arguments match the original
  exactly.
- Removing something that is not currently persisted does
  nothing, so the marker is safe on pages the visitor might
  reach twice.
- The debug panel's footer lists currently persisted components,
  which is the place to look when a removal seems not to land.
- Persistence itself is opt-in per component: `Timer`, `Clock`,
  `Audio`, `Video`, and `Map` all accept `persistent=True`.

## Related components

- [Timer](timer.md) and [Clock](clock.md): the usual persistent
  suspects.
- [Audio](../media/audio.md): the background-music case.

## External links

- [Make things happen over time](../../../add/timers.md): where
  persistence fits in the recipes.
