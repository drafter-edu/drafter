---
page_type: component
title: Video
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Video
outcome: Play video files.
---

# Video

Group: [Media](../index.md#media)

## Description

A `Video` plays a video file with the browser's standard player.
Point it at a file next to your program or a URL, size it if the
natural size is wrong, and the browser does the rest.

## Syntax

```python
Video(src)
Video(src, width=480)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `src` | `str` | required | The video file: a filename next to your program or a URL. |
| `width` | `int` | natural size | Display width in pixels. |
| `height` | `int` | natural size | Display height in pixels. |
| `controls` | `bool` | `True` | Show the player controls. |
| `autoplay` | `bool` | `False` | Start playing when the page finishes loading. |
| `loop` | `bool` | `False` | Start over when it ends. |
| `muted` | `bool` | `False` | Start muted. |
| `persistent` | `bool` | `False` | Keep playing across page changes. |

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
        Header("Training Progress"),
        "Week one: Babbage almost fetches.\n",
        Video("almost_fetching.mp4", width=480)
    ])


start_server(State())
```

(Shown as a listing rather than a live demo because it needs a
video file next to the program.)

## Notes

- Browsers only allow unmuted autoplay after the visitor has
  interacted with the page; `autoplay=True, muted=True` is the
  combination that reliably starts by itself.
- Set only `width` and the height scales to match; setting both
  can stretch the picture.
- Video files are large. One short clip is fine; a gallery of
  them makes the deployed site slow to load, and linking out is
  kinder.
- When deploying, bundle the file with
  `--additional-paths "almost_fetching.mp4"`, or the deployed
  site will [404 on it](../../../help/errors/missing-asset-on-deploy.md).

## Related components

- [Audio](audio.md): sound without the picture.
- [Image](image.md): a picture without the motion.

## External links

- [The video element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/video)
