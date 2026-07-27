---
page_type: reference
title: File types
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - DrafterTextFile
  - DrafterBinaryFile
outcome: Use the upload result types.
---

# File types

When a visitor uploads a file through
[FileUpload](../components/input/fileupload.md), the receiving
route's annotation decides what arrives. The plain annotations
(`str`, `bytes`, [Picture](picture.md)) deliver only the
contents; the two types on this page deliver the contents
*together with* the filename and metadata, for routes that need
to know what was uploaded, not only what was in it.

## Choosing an annotation

| Annotation | The parameter receives |
| ---------- | ---------------------- |
| `str` | The file's contents decoded as text. |
| `bytes` | The raw contents. |
| `Picture` | The file decoded as an image. |
| `DrafterTextFile` | Text contents plus filename and metadata. |
| `DrafterBinaryFile` | Raw contents plus filename and metadata. |

## DrafterTextFile

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `filename` | `str` | The name the file had on the visitor's computer. |
| `content` | `str` | The contents, decoded as UTF-8 text. |
| `content_type` | `str` | The reported MIME type, like `"text/plain"`. |
| `size` | `int` | The size the visitor's browser reported. |

## DrafterBinaryFile

The same four fields, except `content` is `bytes`, and the
default MIME type is `"application/octet-stream"`. Use it for
files that are not text and not images: audio files to hand to a
sound component, or data you will pass along to
[Download](../components/input/download.md) unchanged.

## Example

The filename makes the confirmation page much friendlier than
"upload received":

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Poem Collector"),
        state.report + "\n",
        FileUpload("poem"),
        "\n",
        Button("Submit poem", "receive")
    ])


@route
def receive(state: State, poem: DrafterTextFile) -> Page:
    lines = poem.content.split("\n")
    state.report = (poem.filename + " received: "
                    + str(len(lines)) + " lines, "
                    + str(poem.size) + " bytes.")
    return index(state)


start_server(State("No poems yet."))
```

## Notes

- The text-decoding annotations (`str`, `DrafterTextFile`)
  expect UTF-8. Handing them something that is not text stops the
  route with a friendly error; see the
  [file decode error entry](../../help/errors/file-decode-error.md).
- `size` and `content_type` are reported by the visitor's
  browser. They are fine for display and rough checks, and
  nothing more; the `content` itself is the truth.
- These values sit happily in state, like every type in this
  section, but large files make state large; keep what you need
  (often `content` parsed into your own dataclass) rather than
  the whole envelope.

## Related

- [FileUpload](../components/input/fileupload.md) and
  [Download](../components/input/download.md): files in and out.
- [Upload and download files](../../add/files.md): the recipes.
