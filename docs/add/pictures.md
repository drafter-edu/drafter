---
page_type: how-to
title: Use pictures
level: L3
audience: S
priority: P1
prereqs: [add/ask-for-information]
symbols: []
outcome: Show, upload, and edit images.
---

# Use pictures

## Goal

You want images in your app: shown on pages, uploaded by visitors,
maybe changed by your code.

## Before you start

You can build a form. This page rests on two ideas: the `Image`
component *shows* a picture, while the `Picture` type *is* one, a
value you can store in state, pass to functions, and transform like
any other value.

## Recipe: show an image

`Image` accepts a web address or the name of an image file sitting
next to your program:

```python drafter height=280
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Today's Visitor"),
        Image("https://placehold.co/200x120.png", 200, 120),
        "\nA placeholder guest, 200 by 120."
    ])


start_server()
```

The two numbers are the width and height in pixels. Leave them off
to use the image's own size.

## Recipe: let visitors upload a picture

Annotate the receiving parameter as `Picture | None` and a
`FileUpload` delivers a real `Picture` (or `None` when no file was
chosen):

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    portrait: Picture


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Portrait Studio"),
        state.portrait,
        "\nChoose a new portrait:",
        FileUpload("new_portrait", accept="image/*"),
        "\n",
        Button("Use it", "update")
    ])


@route
def update(state: State, new_portrait: Picture | None) -> Page:
    if new_portrait is not None:
        state.portrait = new_portrait
    return index(state)


start_server(State(Picture.new(160, 120, "lightsteelblue")))
```

A `Picture` placed in the content list displays itself, and
`Picture.new(width, height, color)` creates a blank picture to start
from.

## Recipe: transform a picture

`Picture` values provide transformation methods, each of which
returns a changed copy:

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    art: Picture


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("One-Button Art Studio"),
        state.art,
        "\n",
        Button("Rotate", "spin"),
        Button("Shrink", "shrink"),
        Button("Drain the color", "drain")
    ])


@route
def spin(state: State) -> Page:
    state.art = state.art.rotate(90)
    return index(state)


@route
def shrink(state: State) -> Page:
    state.art = state.art.scale(0.5)
    return index(state)


@route
def drain(state: State) -> Page:
    state.art = state.art.grayscale()
    return index(state)


start_server(State(Picture.new(150, 100, "tomato")))
```

Always assign the result: `state.art.rotate(90)` on its own creates
a rotated copy and then discards it. The full method list is on the
[Picture reference page](../reference/data-types/picture.md).

## Recipe: let visitors keep the result

`Download("Save it", "art.png", state.art)` offers the picture to
the visitor as a file. The
[photo editor example](../examples/photo-editor.md) puts the whole
pipeline together, from upload to transformation to download.

## Variations

- Show image files bundled with your app by name:
  `Image("logo.png")`.
- Build pictures from scratch, pixel by pixel or with drawing
  helpers; the [Picture reference](../reference/data-types/picture.md)
  covers those tools.
- Size with styling instead of pixels:
  `change_width(Image("big.png"), "50%")`.

## Common problems

- **The image file works at home but not deployed**: the file must
  travel with your site; put it in the repository next to `main.py`.
  See [works locally, 404s deployed](../help/errors/missing-asset-on-deploy.md).
- **Upload errors on a non-image**: a file that cannot be decoded
  stops the route with a friendly error naming the parameter.
  `accept="image/*"` steers the file picker toward images but does
  not guarantee an image is chosen.
- **A URL image shows nothing**: the address must point straight at
  an image (ending in .png, .jpg, or another image extension), not
  at a page containing one, and the visitor needs to be online.
- **Transformations seem to do nothing**: the result was not
  assigned back to state.

## Understand it

Pictures are values, like numbers and strings: they can be stored
in state, passed to functions, and compared in tests.
[State](../concepts/state.md) explains the storage half.

## See another example

The [photo editor](../examples/photo-editor.md) covers pictures, and
the [media playground](../examples/playground/media.md) adds sound
and video.

## Look it up

[Picture](../reference/data-types/picture.md),
[Image](../reference/components/media/image.md),
[FileUpload](../reference/components/input/fileupload.md), and
[Download](../reference/components/input/download.md).

## Fix a problem

[Image or file works locally but 404s when deployed](../help/errors/missing-asset-on-deploy.md).
