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

A `FileUpload` is a file-picker input. The visitor chooses a file
from their device, and when the form is submitted, the file's
contents arrive at the route as a parameter. The parameter's type
annotation decides what form the contents take; the full table of
annotations is in the [files how-to](../../../add/files.md).

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

Besides `multiple`, the HTML attributes `FileUpload` recognizes as
keywords are `capture` and `required`. `required=True` adds the
attribute, but a button still runs its route when no file is chosen.
`disabled` is not on that list. Drafter turns a keyword it does not
recognize into a CSS style, which the browser ignores, and it reports
no error. [Plain HTML attributes](../../keyword-attributes.md#plain-html-attributes)
explains the keyword rule.

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

- The parameter's annotation decides how the file is delivered:
  annotate `str` to receive text, `bytes` to receive any file's raw
  data, `Picture` to receive an image, or one of the
  [file types](../../data-types/file-types.md) when the filename
  matters too.
- When the visitor chooses no file, the result also depends on the
  annotation. A `str` parameter receives `""`, and a `bytes`
  parameter receives `b""`. A file type such as `DrafterTextFile`
  receives a file whose `filename` is empty and whose `size` is 0.
  A `Picture` parameter stops with an error page that says no file
  was chosen. Annotate it `Picture | None` to receive `None`
  instead. Adding `| None` to `str` does not change the result,
  which is still `""`.
- `accept` is guidance for the picker, not enforcement; a visitor
  can still choose any file. A file of the wrong type produces a
  [friendly error](../../../help/errors/file-decode-error.md).
- The route runs when a button submits the form, not at the moment
  the file is chosen.

## Accessibility

Label the control with what you expect ("A .txt file of your
story:"), since the browser's built-in "Choose file" text says
nothing about what the file is for.

## Related components

- [Download](download.md): sending files to the visitor instead.
- [Camera](../capture/camera.md): another way to bring pictures
  into the app.
- [Upload and download files](../../../add/files.md) is the how-to
  guide, with a recipe for receiving a file.

## External links

- [The input file type on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/file)
