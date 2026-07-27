---
page_type: component
title: Audio
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Audio
outcome: Play sound files, including across pages.
---

# Audio

Group: [Media](../index.md#media)

## Description

An `Audio` plays a sound file with the browser's standard player:
play button, scrubber, volume. Point it at a file next to your
program or a URL. For playback with effects, volume control from
code, or visualization, the [Sound](../sound/sound.md) component
is the fancier sibling; `Audio` is the plain, dependable one.

## Syntax

```python
Audio(src)
Audio(src, loop=True, persistent=True)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `src` | `str` | required | The audio file: a filename next to your program, a URL, or a data URL. |
| `controls` | `bool` | `True` | Show the player controls. |
| `autoplay` | `bool` | `False` | Start playing when the page finishes loading. |
| `loop` | `bool` | `False` | Start over when it ends. |
| `muted` | `bool` | `False` | Start muted. |
| `persistent` | `bool` | `False` | Keep playing across page changes (background music). |

## Examples

```python
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Ambience Machine"),
        "Rain sounds for napping cats:\n",
        Audio("rain.mp3", loop=True)
    ])


start_server(State())
```

(Shown as a listing rather than a live demo because it needs an
audio file next to the program; copy it and supply your own
`rain.mp3`.)

## Notes

- Browsers refuse to start sound before the visitor has
  interacted with the page, so `autoplay=True` on the very first
  page may stay silent until a click. Music that starts after a
  "Begin" button always works.
- `persistent=True` keeps the same playback running while the
  visitor moves between pages, which is the background-music
  pattern; stop it later with
  [RemovePersistent](../time/removepersistent.md).
- When deploying, bundle the audio file with
  `--additional-paths "rain.mp3"`, or the deployed site will
  [404 on it](../../../help/errors/missing-asset-on-deploy.md).
- A [Recording](../../data-types/audio-types.md)'s `data_url`
  plays here too, though `Sound` is the usual choice for that.

## Related components

- [Sound](../sound/sound.md): playback with effects, code-set
  volume, and visualization.
- [Video](video.md): the same idea with a picture.

## External links

- [The audio element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/audio)
