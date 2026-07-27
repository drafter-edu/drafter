---
page_type: component
title: FileUpload
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - FileUpload
outcome: Receive a file from the user.
---

# FileUpload

Group: [Input](../index.md#input)

## Description

A `FileUpload` is the file-picker input: the visitor chooses a file
from their device, and when the form submits, the file's contents
arrive at the route as a parameter. What type arrives is decided by
the parameter's annotation; the full table is in the
[files how-to](../../../add/files.md).

## Syntax

```python
FileUpload(name)
FileUpload(name, accept="image/*")
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `accept` | `str` | any file | File-type filters for the picker: a MIME pattern (`"image/*"`), extensions (`".txt"`), or several, comma-separated. |

Adding the `multiple` attribute (`FileUpload("photos",
multiple=True)`) lets the visitor pick several files; the parameter
then receives a list.

## Examples

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    length: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Manuscript Weigher"),
        "Last manuscript: " + str(state.length) + " characters.\n",
        FileUpload("manuscript", accept=".txt"),
        "\n",
        Button("Weigh it", "weigh")
    ])


@route
def weigh(state: State, manuscript: str) -> Page:
    state.length = len(manuscript)
    return index(state)


start_server(State(0))
```

## Notes

- Annotation decides delivery: `str` for text, `bytes` for
  anything, `Picture` for images,
  [file types](../../data-types/file-types.md) when the filename
  matters. Add `| None` to make an empty picker deliver `None`.
- `accept` is guidance for the picker, not enforcement; a
  determined visitor can still choose anything, which is why wrong
  types produce [friendly errors](../../../help/errors/file-decode-error.md)
  rather than chaos.
- The route runs when a button submits, not when the file is
  chosen.

## Accessibility

Label the control with what you expect ("A .txt file of your
story:"), since "Choose file" alone says nothing about purpose.

## Related components

- [Download](download.md): files in the other direction.
- [Camera](../capture/camera.md): a different way pictures arrive.

## External links

- [The input file type on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/file)
