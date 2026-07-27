---
page_type: example
title: Photo editor
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Upload and transform images.
---

# Photo editor

## What it does

A tiny photo editor: upload a picture, shrink it, rotate it, drain
its color, download the result. It shows the whole life of an image
in a Drafter app: in through `FileUpload`, living in state as a
`Picture`, changed by transformations, out through `Download`.

## Try it

Upload any image (or play with the starting swatch), then stack some
transformations.

```python drafter height=380
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    photo: Picture


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Photo Editor"),
        "Current photo:\n",
        state.photo,
        "\n",
        Row("New image file:", FileUpload("new_photo", accept="image/*")),
        Button("Upload", "update_photo"),
        "\n",
        Button("Shrink", "shrink_photo"),
        Button("Rotate", "rotate_photo"),
        Button("Grayscale", "grayscale_photo"),
        "\n",
        Download("Download the photo", "photo.png", state.photo)
    ])


@route
def update_photo(state: State, new_photo: Picture | None) -> Page:
    if new_photo is not None:
        state.photo = new_photo
    return index(state)


@route
def shrink_photo(state: State) -> Page:
    state.photo = state.photo.scale(0.5)
    return index(state)


@route
def rotate_photo(state: State) -> Page:
    state.photo = state.photo.rotate(90)
    return index(state)


@route
def grayscale_photo(state: State) -> Page:
    state.photo = state.photo.grayscale()
    return index(state)


assert_equal(
    shrink_photo(State(Picture.new(40, 20, "salmon"))),
    index(State(Picture.new(20, 10, "salmon"))))

start_server(State(Picture.new(60, 40, "salmon")))
```

## The code

The state holds exactly one thing: the current `Picture`. Every
route follows the same rhythm: replace `state.photo` with a
transformed version, then show the page again. `update_photo` is the
only route with a parameter, because it is the only one receiving
something from a form.

## How it works

Three type tricks carry this app:

- **A `Picture` in page content displays itself.** The line
  `state.photo` in the content list renders as an image, no `Image`
  component required (though
  [Image](../reference/components/media/image.md) exists for more
  control).
- **`new_photo: Picture | None`** is how uploads become pictures.
  Annotating the parameter as `Picture` makes Drafter decode the
  uploaded file into one; the `| None` half means "no file chosen"
  arrives as `None` instead of an error, which the route checks
  before replacing anything.
- **Transformations return new pictures.** `scale`, `rotate`, and
  `grayscale` do not change a picture in place; they hand back a
  changed copy, which is why every route assigns:
  `state.photo = state.photo.scale(0.5)`.

The test at the bottom compares whole pages built from two states,
which works because `Picture`s compare by their actual pixels: a
40x20 salmon swatch scaled by half *equals* a 20x10 salmon swatch
made from scratch.

## Make it yours

1. **Modify**: rotate by 45 instead of 90 and see what happens to
   the corners.
2. **Modify**: add a "Tiny" button that scales by 0.1, and an
   "Undo-ish" button that scales by 2.0 (and notice why that is not
   really undo).
3. **Complete**: add a `flip` button; check the
   [Picture reference](../reference/data-types/picture.md) for the
   method.
4. **Combine**: keep `original: Picture` in state alongside `photo`,
   set it on upload, and add a real "Reset" button.
5. **Create**: a meme maker: this app plus a `TextBox` and the
   Picture reference's text-drawing tools.

## Tests

One `assert_equal` covers the transformation pipeline: shrinking a
known swatch produces exactly the page that a half-size swatch would
produce. Pixel-level equality makes image code surprisingly
testable; build small `Picture.new(...)` swatches in tests rather
than loading files.

## Likely errors

- **Uploading a non-image**: a file that cannot be decoded as an
  image stops the route with a friendly conversion error naming the
  parameter. The `accept="image/*"` on the `FileUpload` steers the
  file picker toward images but is a convenience, not a guarantee.
- **Forgetting the `| None`**: with plain `Picture`, pressing Upload
  with no file chosen becomes an error instead of a quiet no-op.
- **Expecting transformations to mutate**: `state.photo.rotate(90)`
  alone does nothing visible; without the assignment, the rotated
  copy is thrown away.
- **Deploying and losing the photo**: state resets on reload like
  always; a deployed editor starts from the built-in swatch, not
  from anything a visitor uploaded last time.

## Related

- [Use pictures](../add/pictures.md): the how-to for images
  end-to-end.
- [Picture](../reference/data-types/picture.md): every
  transformation and constructor.
- [FileUpload](../reference/components/input/fileupload.md) and
  [Download](../reference/components/input/download.md): the doors
  in and out.
