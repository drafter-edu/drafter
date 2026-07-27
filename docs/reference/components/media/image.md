---
page_type: component
title: Image
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Image
outcome: Show images from a URL, file, Picture, or bytes.
---

# Image

Group: [Media](../index.md#media)

## Description

An `Image` shows a picture on the page. The picture can come from a
web address, an image file next to your program, a
[Picture](../../data-types/picture.md) value in state, or raw
bytes. A bare `Picture` in a content list already displays itself;
use the `Image` wrapper when you want size control or alt text.

## Syntax

```python
Image(url)
Image(url, width, height)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `url` | `str`, `Picture`, `bytes`, or PIL image | required | The image source. Strings are web addresses or local file names. |
| `width` | `int` | image's own | Display width in pixels. |
| `height` | `int` | image's own | Display height in pixels. |

The `alt` attribute sets the text description
(`Image("ada.png", alt="Ada the corgi mid-zoom")`).

## Examples

```python drafter height=280
from drafter import *


@route
def index() -> Page:
    swatch = Picture.new(120, 80, "cadetblue")
    return Page([
        Header("Gallery of One"),
        Image(swatch, alt="A calm blue rectangle"),
        "\nThe same picture, small: ",
        Image(swatch, 30, 20, alt="The same rectangle, tiny")
    ])


start_server()
```

## Notes

- **Sizing here is display-only**: `Image(pic, 30, 20)` changes how
  large the picture appears without changing its pixels;
  `pic.scale(...)`
  [actually resizes it](../../data-types/picture.md).
- **Local file names** work in development, but keep working after
  deployment only if the file ships with the site; see
  [works locally, 404s deployed](../../../help/errors/missing-asset-on-deploy.md).
- **URL images** require the visitor to be online, and the address
  must point directly at an image file.
- A width and height that do not match the picture's proportions
  will stretch it. Give only one of the two, or keep the pair in
  proportion, unless the distortion is intentional.

## Accessibility

Every meaningful image deserves `alt` text describing what it
*shows*, not that it is an image ("Ada asleep on the keyboard",
not "photo"). Purely decorative images can use `alt=""` so screen
readers skip them.

## Related components

- [Picture](../../data-types/picture.md): the value type behind
  most images.
- [Use pictures](../../../add/pictures.md): a how-to guide for
  working with pictures.
- [Camera](../capture/camera.md): captures images from the
  visitor's camera.

## External links

- [The img element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/img)
