---
page_type: component
title: Tone
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Tone
outcome: Play a single note.
---

# Tone

Group: [Sound](../index.md#sound)

## Description

A `Tone` plays one pitch: a beep, a note, a buzz. Name the pitch
like a piano key (`"C4"`, `"F#3"`) or give a frequency in Hz
(`440`), pick a waveform for the character, and the browser
synthesizes it with no sound files involved. It renders as a
small play button unless you make it automatic.

## Syntax

```python
Tone(pitch)
Tone(pitch, duration=1000, waveform="square")
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `pitch` | `str` or number | required | A note name like `"C4"` (middle C) or a frequency in Hz like `440`. |
| `duration` | `int` | `500` | How long it plays, in milliseconds. |
| `waveform` | `str` | `"sine"` | The sound's character: `"sine"` (smooth), `"square"` (buzzy), `"triangle"` (mellow), or `"sawtooth"` (bright). |
| `volume` | `float` | `0.8` | Loudness from 0.0 to 1.0. |
| `attack` | `int` | `10` | Milliseconds of fade-in. |
| `release` | `int` | `50` | Milliseconds of fade-out. |
| `auto_play` | `bool` | `False` | Play when the page loads instead of showing a button. |
| `show` | `bool` | `True` | Display the component. |
| `effects` | list of effects | none | [Audio effects](effects.md) applied in order. |
| `on_start` / `on_finish` / `on_error` | `str` | none | Routes to call as playback starts, ends, or fails. |

## Examples

The same note in all four characters:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Four Waveforms"),
        "Same pitch, four personalities:\n",
        "Smooth ", Tone("A4", waveform="sine"),
        " Buzzy ", Tone("A4", waveform="square"),
        " Mellow ", Tone("A4", waveform="triangle"),
        " Bright ", Tone("A4", waveform="sawtooth")
    ])


start_server(State())
```

## Notes

- Note names run letter, optional `#`, octave: `"C4"` is middle
  C, `"A4"` the tuning A. Frequencies work when you want math to
  choose the pitch.
- Browsers refuse sound before the visitor interacts with the
  page, so an `auto_play` tone on the very first page shows an
  "Enable sound" prompt instead. Tones on later pages, after
  clicks, play freely.
- `auto_play=True, show=False` is the sound-effect pattern: a
  route returns a page containing an invisible automatic tone,
  and the arrival plays it.
- A wrong waveform or an unpronounceable pitch stops the page
  with a friendly error listing the valid choices.

## Related components

- [Melody](melody.md): a sequence of tones with rhythm.
- [Sound](sound.md): playing audio files instead of synthesized
  pitches.

## External links

- [Note names and frequencies](https://en.wikipedia.org/wiki/Scientific_pitch_notation)
