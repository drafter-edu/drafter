---
page_type: component
title: Melody
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Melody
outcome: Play a note sequence.
---

# Melody

Group: [Sound](../index.md#sound)

## Description

A `Melody` plays a list of notes in rhythm. Each item is a note
name (one beat), a `(note, beats)` pair for longer or shorter
notes, or `"rest"` for silence; a tempo sets the speed. The notes
are scheduled with precise audio timing, so melodies hold their
rhythm even while the page is busy.

## Syntax

```python
Melody(["C4", "E4", "G4"])
Melody([("C4", 2), "D4", "rest", ("E4", 0.5)], tempo=90)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `notes` | `list` | required | Note names, `(note, beats)` pairs, and `"rest"`s, in order. |
| `tempo` | number | `120` | Speed in beats per minute. |
| `waveform` | `str` | `"sine"` | The sound character, as on [Tone](tone.md). |
| `volume` | `float` | `0.8` | Loudness from 0.0 to 1.0. |
| `auto_play` | `bool` | `False` | Play on page load instead of showing a button. |
| `controls` | `bool` | `False` | Show play/pause and restart buttons. |
| `show` | `bool` | `True` | Display the component. |
| `effects` | list of effects | none | [Audio effects](effects.md) applied in order. |
| `on_note` / `on_finish` | `str` | none | Routes to call as each note starts and when the melody ends. |

## Examples

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Dinner Bell"),
        "The song that summons every pet in the house:\n",
        Melody([("C4", 1), ("E4", 1), ("G4", 1), ("C5", 2),
                "rest", ("G4", 0.5), ("C5", 2.5)],
               tempo=140, waveform="triangle", controls=True)
    ])


start_server(State())
```

## Notes

- Beats can be fractions: `("C4", 0.5)` is half a beat,
  `("C4", 2)` a held note. `None` in the list also counts as a
  rest.
- An `on_note` route that returns a whole `Page` re-renders the
  page and resets the melody after its first note; return an
  `Update` or a `Fragment` to react while the music continues,
  and save full pages for `on_finish`.
- Melodies live happily in state as plain lists, which means a
  program can compose: build the list with a loop, then hand it
  to `Melody`.
- The browser's require-an-interaction rule applies as with
  [Tone](tone.md): automatic playback on the first page shows an
  enable prompt.

## Related components

- [Tone](tone.md): one note at a time.
- [Audio effects](effects.md): echo and reverb over the whole
  melody.

## External links

- [Note names and frequencies](https://en.wikipedia.org/wiki/Scientific_pitch_notation)
