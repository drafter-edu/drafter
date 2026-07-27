---
page_type: component
title: Audio effects
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Echo
  - Reverb
  - Muffle
  - Sharpen
  - Distortion
outcome: Apply audio effects to sounds.
---

# Audio effects

Group: [Sound](../index.md#sound)

## Description

Five effects reshape how a sound plays. They are plain values,
not components: build a list of them and pass it as the
`effects` argument of [Sound](sound.md), [Tone](tone.md), or
[Melody](melody.md), and they apply in order. Each effect has
one or two number settings, all with sensible defaults, so
`effects=[Echo()]` already works.

## Syntax

```python
Sound("clip.mp3", effects=[Echo()])
Melody(["C4", "E4"], effects=[Muffle(0.7), Reverb(amount=0.6)])
```

## Parameters

| Effect | Settings | What it does |
| ------ | -------- | ------------ |
| `Echo` | `delay` (seconds between repeats, default 0.3), `strength` (how loud each repeat is, 0.0-1.0, default 0.4) | Repeats the sound, quieter each time. |
| `Reverb` | `amount` (0.0-1.0, default 0.5) | Lets the sound ring out, as if in a large room. |
| `Muffle` | `amount` (0.0-1.0, default 0.5) | Removes high frequencies, like sound through a wall. |
| `Sharpen` | `amount` (0.0-1.0, default 0.5) | Removes low frequencies, like a tinny speaker. |
| `Distortion` | `amount` (0.0-1.0, default 0.3) | Overdrives the sound for a gritty character. |

## Examples

One melody, plain and processed:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


NOTES = [("E4", 0.5), ("G4", 0.5), ("A4", 2)]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Effect Test Bench"),
        "Plain: ", Melody(NOTES),
        "\nHaunted: ", Melody(NOTES, effects=[Echo(delay=0.4),
                                              Reverb(amount=0.7)]),
        "\nThrough the wall: ", Melody(NOTES,
                                       effects=[Muffle(0.8)]),
        "\nBroken radio: ", Melody(NOTES,
                                   effects=[Distortion(0.6),
                                            Sharpen(0.6)])
    ])


start_server(State())
```

## Notes

- Order matters: `[Echo(), Distortion()]` distorts the echoes,
  while `[Distortion(), Echo()]` echoes the distortion. Small
  difference here, bigger with stronger settings.
- The `effects` argument must be a list even for one effect, and
  every item needs its parentheses (`Echo()`, not `Echo`); the
  friendly errors for both mistakes say so.
- Settings outside 0.0-1.0 (except `Echo`'s `delay`, which is
  seconds) are rejected when the component is built.
- Effects change playback only; the underlying file or
  [Recording](../../data-types/audio-types.md) is untouched.

## Related components

- [Sound](sound.md), [Tone](tone.md), and [Melody](melody.md):
  the three components that accept `effects`.
