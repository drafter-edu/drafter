---
page_type: reference
title: Photo
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Photo
outcome: Use the camera result type.
---

# Photo

A `Photo` is the value a [Camera](../components/capture/camera.md)
component submits: the captured image, wrapped together with the
information about whether capturing actually happened. Annotate a
route parameter with `Photo` when your route needs to handle the
visitor declining the camera as gracefully as it handles a
successful shot.

## Fields

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `status` | `str` | Where the camera workflow stands; see the table below. |
| `message` | `str` or `None` | A description accompanying an error or denial, when there is one. |
| `data_url` | `str` or `None` | The captured photo as a PNG data URL, or `None` when nothing has been captured. |
| `width` | `int` or `None` | Width of the captured photo in pixels. |
| `height` | `int` or `None` | Height of the captured photo in pixels. |

The `picture` property is the convenient door out: it decodes the
photo into a [Picture](picture.md) value ready for
[Image](../components/media/image.md), transformations, or state,
and it is `None` whenever nothing has been captured.

## Statuses

| `status` | Meaning |
| -------- | ------- |
| `"prompt"` | The visitor has not been asked for the camera yet. |
| `"pending"` | Waiting on the permission dialog. |
| `"live"` | Preview running, no photo taken yet. |
| `"granted"` | A photo has been captured. |
| `"denied"` | The visitor refused camera access. |
| `"error"` | The camera failed. |
| `"unavailable"` | The device has no usable camera API. |

Only `"granted"` comes with an image; treat every other status as
"no photo, and here is why".

## Receiving one

```python
@route
def save_photo(state: State, shot: Photo) -> Page:
    if shot.picture is None:
        return Page(state, ["No photo (" + shot.status + ")."])
    state.portrait = shot.picture
    return index(state)
```

Checking `shot.picture is None` covers every non-granted status at
once, which is usually all a route needs.

## Notes

- If your route cannot do anything useful without an image,
  annotate the parameter as [Picture](picture.md) (or `bytes`)
  instead; Drafter unwraps the photo for you and stops with a
  friendly error when there is none. `Photo` is for routes that
  want to handle the empty case themselves.
- Building a `Picture` from a `Photo` with no image raises a
  friendly error naming the status, so the `None` check above is
  the pattern to keep.
- Like the other capture types, failures arrive as values, never
  as exceptions; no `try`/`except` is needed anywhere.

## Related

- [Camera](../components/capture/camera.md): the component that
  produces these values.
- [Picture](picture.md): what the image becomes once unwrapped.
