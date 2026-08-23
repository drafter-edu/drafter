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

You want to move files across your app's boundary: visitors handing
files in, your app handing files out, and your code reading data
files that were bundled with it.

## Before you start

You can build a form. One mental adjustment is needed: your app
lives in the browser, so "files" means the visitor's files (which
they must explicitly choose) and files bundled with your app. Your
code cannot browse a hard drive on its own.

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

Each annotation produces a different kind of value:

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

`Download` works in the opposite direction: it offers text (or
bytes) your app built as a file the visitor can save.

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

The three arguments are the link text, the filename to save as, and
the contents. Rebuild the contents every time the page renders, as
this example does, so the download always reflects the current
state.

## Recipe: read a bundled data file

Plain `open()` works for files that ship with your app:

```python
with open("questions.txt") as data_file:
    lines = data_file.readlines()
```

Keep the file next to your program. When you deploy, the file must
be deployed too: upload it to the repository, and tell the build
about it with `add_website_file`, which also checks right away that
the file really exists (and suggests similarly named files if not):

```python
add_website_file("questions.txt")
```

The `--additional-paths` command line flag does the same job from
outside the code, repeated once per file (see
[Command line](../reference/cli.md)).
The helper `get_drafter_path("questions.txt")` resolves a name to
wherever the app's files actually live, which helps in the rare
case where plain `open` cannot find a file you bundled.

## Variations

- If uploaded text may contain unusual characters, annotate the
  parameter as `bytes` and decode it deliberately, or accept the
  friendly error; see
  [Uploaded file couldn't be read as text](../help/errors/file-decode-error.md).
- To offer structured data as a download, build CSV text with a
  loop (`row = name + "," + str(score)`) and give the file a `.csv`
  name so spreadsheet programs can open it.

## Common problems

- **Reading before uploading**: the route runs only when the button
  is pressed, and the parameter holds the file chosen *then*.
  Nothing arrives ahead of time.
- **`str` upload errors on a binary file**: a file that is not
  text cannot arrive as `str`. Annotate the parameter as `bytes`,
  or steer the picker toward text files with `accept=".txt"`.
- **A bundled file 404s after deploy**: it never made it into the
  repository, or the name differs in case. See
  [works locally, 404s deployed](../help/errors/missing-asset-on-deploy.md).
- **Nothing survives reload**: files a visitor uploads live in
  state, and state resets on reload as it always does. The download
  button is how visitors keep a permanent copy.

## Understand it

[How Drafter works](../start/how-drafter-works.md) explains that
the app runs entirely inside the browser tab, which is why files
must be explicitly handed in and out.

## See another example

The [photo editor](../examples/photo-editor.md) runs the whole
upload-and-download loop for images.

## Look it up

[FileUpload](../reference/components/input/fileupload.md),
[Download](../reference/components/input/download.md), and
[File types](../reference/data-types/file-types.md).

## Fix a problem

[Uploaded file couldn't be read as text](../help/errors/file-decode-error.md)
and
[works locally, 404s deployed](../help/errors/missing-asset-on-deploy.md).
