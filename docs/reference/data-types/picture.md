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

A `Picture` is an image represented as a Python value. You can store
one in state, pass it to functions, transform it, and compare it in
tests by its actual pixels. When you put a `Picture` in a page's
content list, the page displays it as an image; when you annotate a
route parameter with `Picture`, uploaded images arrive already
decoded. For step-by-step instructions, see
[Use pictures](../../add/pictures.md).

## Making pictures

| Call | Makes |
| ---- | ----- |
| `Picture.new(width, height, color)` | A solid swatch of one color; `color` defaults to white. This constructor is especially useful in tests. |
| `Picture("photo.png")` | From a file next to your program, a URL, or raw bytes; the constructor detects which kind of value you passed. |
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

URL pictures are **lazy**: the image is not fetched when the
`Picture` is constructed, but when it is first needed. Building a
page full of URL pictures is therefore fast, and a bad URL causes an
error when the picture is displayed or transformed, not when it is
constructed.

## Size

Use `picture.width` and `picture.height` to get a picture's size in
pixels. Both are properties, so they are written without
parentheses.

## Transformations

Every transformation returns a **new** `Picture` and leaves the
original unchanged, so remember to assign the result to a variable.

| Method | Effect |
| ------ | ------ |
| `resize(width, height)` | Resizes to exactly the given size, stretching the image if needed. |
| `scale(factor)` | Scales proportionally: `scale(0.5)` halves the size, `scale(2)` doubles it. |
| `rotate(degrees)` | Rotates counterclockwise; the canvas grows to fit the corners. |
| `crop(left, top, right, bottom)` | Keeps only the box between those pixel edges. |
| `flip_horizontal()` / `flip_vertical()` | Mirrors the image. |
| `grayscale()` | Converts the image to shades of gray. |

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

Two methods support pixel-by-pixel work:

- `get_pixel(x, y)` returns the color at that spot as an
  `(r, g, b)` tuple of 0-255 values.
- `set_pixel(x, y, color)` changes one pixel in place (the one
  operation that mutates rather than copies).

Coordinates start at `(0, 0)` in the top-left corner. Out-of-range
coordinates raise a friendly error that names the valid range.

## Converting out

| Method | Produces |
| ------ | -------- |
| `to_bytes()` | Raw image bytes, for [Download](../components/input/download.md) or files. |
| `to_data_url()` | A `data:` URL string. |
| `to_pil()` | A PIL/Pillow image, for library features beyond the methods listed here. |
| `save(path)` | Writes an image file (development-side use). |

## Equality

Two pictures are equal when their pixels are equal, regardless of
how each picture was made. This rule is what makes image code
testable:

```python
assert_equal(Picture.new(40, 20, "salmon").scale(0.5),
             Picture.new(20, 10, "salmon"))
```

## Notes

- **In content lists**, a bare `Picture` renders as an image. Wrap
  it in [Image](../components/media/image.md) when you need to
  control the width, height, or alt text.
- **As a parameter annotation**, `Picture` decodes an upload (or a
  [camera](../components/capture/camera.md) capture). Add
  `| None` so that "no file chosen" arrives as `None`.
- **PIL/Pillow compatibility** works in both directions (`from_pil`,
  `to_pil`), so v1-era PIL code and tutorials still work.
- **Color names** are the same
  [HTML color names](../colors.md) that styling uses; hex strings
  also work.

## Related

- [Use pictures](../../add/pictures.md): the how-to guide for
  working with pictures.
- [Photo editor](../../examples/photo-editor.md): a complete worked
  example built around pictures.
- [Image](../components/media/image.md),
  [FileUpload](../components/input/fileupload.md),
  [Download](../components/input/download.md): the components that
  display, upload, and download pictures.
