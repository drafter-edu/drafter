---
page_type: reference
title: Picture
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Picture
outcome: Use the full Picture API.
---

# Picture

A `Picture` is an image as a Python value: storable in state,
passable to functions, transformable, and comparable in tests by
its actual pixels. Put one in a page's content list and it displays
itself; annotate a route parameter with it and uploads arrive
decoded. The how-to is [Use pictures](../../add/pictures.md).

## Making pictures

| Call | Makes |
| ---- | ----- |
| `Picture.new(width, height, color)` | A solid swatch; `color` defaults to white. The workhorse for tests. |
| `Picture("photo.png")` | From a file next to your program, or a URL, or raw bytes; the constructor detects what you gave it. |
| `Picture.from_file(path)` | Explicitly from a file. |
| `Picture.from_url(url)` | Explicitly from a web address. |
| `Picture.from_bytes(data)` | From raw image bytes. |
| `Picture.from_data_url(url)` | From a `data:` URL. |
| `Picture.from_pil(image)` | From a PIL/Pillow image. |

```python drafter height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Three swatches"),
        Picture.new(80, 50, "salmon"),
        Picture.new(80, 50, "lightseagreen"),
        Picture.new(80, 50, "navajowhite")
    ])


start_server()
```

URL pictures are **lazy**: the image is fetched when first needed,
not when constructed, so building a page of URL pictures is cheap
and a bad URL fails at display or transformation time, not at
construction.

## Size

`picture.width` and `picture.height`, in pixels, as properties (no
parentheses).

## Transformations

Every transformation returns a **new** `Picture`; the original is
untouched. Assign the result.

| Method | Effect |
| ------ | ------ |
| `resize(width, height)` | Exact new size, stretching if needed. |
| `scale(factor)` | Proportional: `scale(0.5)` halves, `scale(2)` doubles. |
| `rotate(degrees)` | Counterclockwise; the canvas grows to fit corners. |
| `crop(left, top, right, bottom)` | Keep the box between those pixel edges. |
| `flip_horizontal()` / `flip_vertical()` | Mirror. |
| `grayscale()` | Drain the color. |

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    original = Picture.new(90, 60, "mediumpurple")
    return Page([
        Header("One swatch, transformed"),
        original,
        original.scale(0.5),
        original.rotate(45),
        original.grayscale()
    ])


start_server()
```

## Pixels

For pixel-by-pixel work:

- `get_pixel(x, y)` returns the color at that spot as an
  `(r, g, b)` tuple of 0-255 values.
- `set_pixel(x, y, color)` changes one pixel in place (the one
  operation that mutates rather than copies).

Coordinates run from `(0, 0)` at the top-left; out-of-range
coordinates raise a friendly error naming the valid range.

## Converting out

| Method | Produces |
| ------ | -------- |
| `to_bytes()` | Raw image bytes, for [Download](../components/input/download.md) or files. |
| `to_data_url()` | A `data:` URL string. |
| `to_pil()` | A PIL/Pillow image, for library work beyond the curated methods. |
| `save(path)` | Writes an image file (development-side use). |

## Equality

Two pictures are equal when their pixels are equal, regardless of
how each was made. That is what makes image code testable:

```python
assert_equal(Picture.new(40, 20, "salmon").scale(0.5),
             Picture.new(20, 10, "salmon"))
```

## Notes

- **In content lists**, a bare `Picture` renders as an image; wrap
  it in [Image](../components/media/image.md) when you need
  width/height or alt text control.
- **As a parameter annotation**, `Picture` decodes an upload (or a
  [camera](../components/capture/camera.md) capture); add
  `| None` so "no file chosen" arrives as `None`.
- **PIL/Pillow compatibility** runs both directions (`from_pil`,
  `to_pil`), so v1-era PIL code and tutorials still work.
- **Color names** are the same
  [HTML color names](../colors.md) styling uses, plus hex strings.

## Related

- [Use pictures](../../add/pictures.md): the how-to.
- [Photo editor](../../examples/photo-editor.md): the worked
  example.
- [Image](../components/media/image.md),
  [FileUpload](../components/input/fileupload.md),
  [Download](../components/input/download.md): the components a
  Picture flows through.
