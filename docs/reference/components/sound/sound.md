---
page_type: component
title: Sound
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Sound
outcome: Play files through effects.
---

# Sound

Group: [Sound](../index.md#sound)

## Description

A `Sound` plays an audio file through a processing chain: set
its volume and stereo position from code, slow it down or speed
it up, run it through [effects](effects.md) like echo and
reverb, and optionally draw a live visualization while it plays.
The plain [Audio](../media/audio.md) component plays files too;
`Sound` is for when the playback itself is part of the app.

## Syntax

```python
Sound(src)
Sound(src, volume=0.5, speed=1.5, effects=[Echo()])
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `src` | `str` | required | The audio: a filename next to your program, a URL, or a data URL (including a [Recording](../../data-types/audio-types.md)'s). |
| `volume` | `float` | `1.0` | Loudness from 0.0 to 1.0. |
| `pan` | `float` | `0.0` | Stereo position from -1.0 (left) to 1.0 (right). |
| `speed` | `float` | `1.0` | Playback speed; below 1.0 is slower and deeper, above is faster and higher. |
| `loop` | `bool` | `False` | Repeat forever. |
| `effects` | list of effects | none | [Audio effects](effects.md) applied in order. |
| `auto_play` | `bool` | `False` | Start when the page loads. |
| `controls` | `bool` | `True` | Show playback controls. |
| `visualize` | `str` | none | Draw the sound live: `"waveform"` or `"bars"`. |
| `on_play` / `on_finish` / `on_error` | `str` | none | Routes to call as playback starts, ends, or fails. |

## Examples

A recording played back three ways (record something first):

```python drafter height=420
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clip: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Echo Cave"),
        "Record a shout, then choose your cave:\n",
        AudioRecorder("shout"),
        "\n",
        Button("Enter the cave", "cave")
    ])


@route
def cave(state: State, shout: Recording) -> Page:
    if shout.data_url is None:
        return Page(state, [
            "Record something first!\n",
            Button("Back", "index")
        ])
    state.clip = shout.data_url
    return Page(state, [
        Header("Choose your acoustics"),
        "Small cave: ",
        Sound(state.clip, effects=[Echo(delay=0.2, strength=0.3)]),
        "\nVast cavern: ",
        Sound(state.clip, effects=[Reverb(amount=0.8)]),
        "\nChipmunk ledge: ",
        Sound(state.clip, speed=1.8),
        "\n",
        Button("Record another", "index")
    ])


start_server(State(""))
```

## Notes

- Everything is set at render time: a route changes the volume
  by re-rendering with a different `volume` value, usually from
  state.
- `visualize="bars"` draws a small live frequency display, a
  nice touch for music apps.
- The browser's require-an-interaction rule applies to
  `auto_play` here as everywhere in this group.
- File sources need bundling at deploy time with
  `--additional-paths`, like [Audio](../media/audio.md); data
  URLs from recordings need nothing extra.

## Related components

- [Audio](../media/audio.md): plain playback without the
  processing chain.
- [AudioRecorder](audiorecorder.md): where recordings come from.
- [Audio effects](effects.md): the five effects.

## External links

- [Audio types](../../data-types/audio-types.md): the
  `Recording` value.
