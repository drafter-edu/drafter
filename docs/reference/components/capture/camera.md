---
page_type: component
title: Camera
level: L4
audience: S
priority: P1
prereqs: []
symbols:
  - Camera
  - Photo
outcome: Take a photo into the app.
---

# Camera

Group: [Capture](../index.md#capture)

## Description

A `Camera` lets the visitor take a photo with their webcam and
submit it with the form. It shows an "Enable camera" button; once
the visitor grants permission, a live preview appears with a "Take
photo" button. The captured photo is submitted under the
component's name, and the receiving route chooses what to get: a
`Photo` (the full record, including whether permission was
granted) or a [Picture](../../data-types/picture.md) (just the
image, ready to display or edit).

## Syntax

```python
Camera(name)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `width` | `int` | `640` | Requested preview and photo width, in pixels. |
| `height` | `int` | `480` | Requested preview and photo height, in pixels. |
| `facing` | `str` | `"user"` | Which camera to prefer on phones: `"user"` (front, selfie) or `"environment"` (rear). |
| `mirror` | `bool` | `True` | Mirror the live preview like a selfie mirror. The captured photo is never mirrored. |
| `show` | `bool` | `True` | Display the camera UI. |
| `on_capture` | `str` | none | Route to call when a photo is taken. |
| `on_denied` | `str` | none | Route to call when the visitor refuses permission. |
| `on_error` | `str` | none | Route to call when the camera fails. |

## Examples

With a `Photo` annotation, the route receives the full record and
can check whether a photo actually exists before showing it. The
`picture` property is the image as a `Picture`, or `None` when
nothing was captured:

```python drafter height=460
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet Portrait Studio"),
        "Hold your pet up to the camera!\n",
        Camera("shot"),
        "\n",
        Button("Save portrait", "portrait")
    ])


@route
def portrait(state: State, shot: Photo) -> Page:
    if shot.picture is None:
        return Page(state, [
            "No photo yet (" + shot.status + "). Go back and "
            "take one!\n",
            Button("Back", "index")
        ])
    return Page(state, [
        Header("A masterpiece"),
        Image(shot.picture),
        "\n",
        Button("Take another", "index")
    ])


start_server(State())
```

With a `Picture` annotation, the route gets the image directly and
can use every `Picture` transformation:

```python drafter height=520
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Photo Booth"),
        Camera("snapshot", facing="user"),
        "\n",
        Button("Develop", "develop")
    ])


@route
def develop(state: State, snapshot: Picture) -> Page:
    return Page(state, [
        Header("Your prints"),
        Image(snapshot.grayscale()),
        Image(snapshot.flip_horizontal()),
        "\n",
        Button("New photo", "index")
    ])


start_server(State())
```

## Notes

- A `Photo` carries `status`, an optional `message`, the photo's
  `width` and `height`, and the `picture` property. The `status`
  is `"granted"` once a photo has been taken, `"denied"` when
  permission was refused, and `"prompt"`, `"pending"`, `"live"`,
  `"error"`, or `"unavailable"` along the way.
- The `Picture` annotation is the convenient path, but if the
  visitor never took a photo, the route stops with a friendly
  error. Use the `Photo` annotation when you want to handle that
  case yourself, as the first example does.
- After a photo is taken, the camera stream stops (and the
  camera light turns off); "Retake" starts it again.
- Store a captured `Picture` in state to keep it across pages, and
  hand it to [Download](../input/download.md) to let
  the visitor save it.
- Ask for the camera only when your app really uses it, and make
  it obvious what happens to the photos. In a Drafter app they
  stay on the visitor's own computer unless your code offers them
  for download.

## Related components

- [Image](../media/image.md): display the captured photo.
- [FileUpload](../input/fileupload.md): receive an existing image
  file instead of taking a new one.

## External links

- [The Picture data type](../../data-types/picture.md)
- [The Photo data type](../../data-types/photo.md)
