---
page_type: how-to
title: Upload and download files
level: L3
audience: S
priority: P1
prereqs: [add/ask-for-information]
symbols:
  - open
  - get_drafter_path
outcome: Move files in and out of the app.
---

# Upload and download files

## Goal

You want files crossing your app's boundary: visitors handing files
in, your app handing files out, and your code reading data files it
shipped with.

## Before you start

You can build a form. The one mental adjustment: your app lives in
the browser, so "files" means the visitor's files (which they must
explicitly choose) and files bundled with your app, not a hard
drive your code can wander.

## Recipe: receive a file

A `FileUpload` component delivers the chosen file to a route
parameter; the parameter's type annotation decides what arrives.

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    poem: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Poem Inspector"),
        "The current poem has " + str(len(state.poem)) + " characters.\n",
        "Upload a text file:",
        FileUpload("poem_file", accept=".txt"),
        "\n",
        Button("Inspect", "inspect")
    ])


@route
def inspect(state: State, poem_file: str) -> Page:
    state.poem = poem_file
    return Page(state, [
        "The file begins: " + state.poem[:40] + "\n",
        Link("Back", "index")
    ])


start_server(State(""))
```

The annotation table:

| Annotation | What the route receives |
| ---------- | ----------------------- |
| `str` | The file's contents as text. |
| `bytes` | The raw bytes, for any file type. |
| `Picture` | An image, decoded; see [Use pictures](pictures.md). |
| `DrafterTextFile` / `DrafterBinaryFile` | Contents plus the filename and metadata; see [File types](../reference/data-types/file-types.md). |

Add `| None` to any of them to make "no file chosen" arrive as
`None` instead of an error. A `FileUpload` with the `multiple`
attribute delivers a list.

## Recipe: offer a download

`Download` is the reverse door: text (or bytes) your app built,
offered as a file.

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    entries: list[str]


@route
def index(state: State) -> Page:
    journal = ""
    for entry in state.entries:
        journal = journal + entry + "\n"
    return Page(state, [
        Header("Field Journal"),
        BulletedList(state.entries),
        "New entry:",
        TextBox("entry"),
        "\n",
        Button("Record", "record"),
        "\n",
        Download("Download the journal", "journal.txt", journal)
    ])


@route
def record(state: State, entry: str) -> Page:
    state.entries.append(entry)
    return index(state)


start_server(State(["Day 1: Captain ignored me."]))
```

The three arguments: link text, the filename to save as, and the
contents. Rebuild the contents each render, as here, so the
download always reflects the current state.

## Recipe: read a bundled data file

Plain `open()` works for files that ship with your app:

```python
with open("questions.txt") as data_file:
    lines = data_file.readlines()
```

Keep the file next to your program. When you deploy, it must travel
too: upload it to the repository, and if the build needs telling,
the `--additional-paths` flag lists extra files to bundle (see
[Command line](../reference/cli.md)). The helper
`get_drafter_path("questions.txt")` resolves a name to wherever the
app's files actually live, useful in the rare case plain `open`
cannot find what you bundled.

## Variations

- Uploaded text with unusual characters: annotate `bytes` and
  decode deliberately, or accept the friendly error; see
  [Uploaded file couldn't be read as text](../help/errors/file-decode-error.md).
- Downloads of structured data: build CSV text with a loop
  (`row = name + "," + str(score)`), name the file `.csv`, and
  spreadsheets open it.

## Common problems

- **Reading before uploading**: the route runs only when the button
  is pressed, and the parameter holds the file chosen *then*.
  Nothing arrives ahead of time.
- **`str` upload errors on a binary file**: a file that is not
  text cannot arrive as `str`; annotate `bytes` (or catch it in
  design: `accept=".txt"`).
- **A bundled file 404s after deploy**: it never made it into the
  repository, or the name differs in case. See
  [works locally, 404s deployed](../help/errors/missing-asset-on-deploy.md).
- **Nothing survives reload**: files a visitor uploads live in
  state, and state resets on reload like always. The download
  button is how visitors keep things.

## Understand it

[How Drafter works](../start/how-drafter-works.md): the app's whole
world lives in the browser tab, which is why files must be
explicitly handed in and out.

## See another example

The [photo editor](../examples/photo-editor.md) runs the whole
loop for images.

## Look it up

[FileUpload](../reference/components/input/fileupload.md),
[Download](../reference/components/input/download.md), and
[File types](../reference/data-types/file-types.md).

## Fix a problem

[Uploaded file couldn't be read as text](../help/errors/file-decode-error.md)
and
[works locally, 404s deployed](../help/errors/missing-asset-on-deploy.md).
