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

When the visitor presses the button without choosing a file, a `str`
parameter receives an empty string and a `bytes` parameter receives
empty bytes, so check for an empty value before using it. A `Picture`
parameter has no empty form and shows an error instead, unless you
annotate it as `Picture | None`, in which case it receives `None`. A
`FileUpload` with the `multiple` attribute delivers a list.

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
be deployed too. If you publish with the template from
[Publish on GitHub Pages](../your-project/deploy/github-pages.md),
upload the file to the repository next to `main.py`, and the
template includes it in the site along with every other file in the
repository.

If you build the site another way, tell the build about the file
with `add_website_file`. That function also checks right away that
the file really exists, and stops the program with a "file not
found" message if it does not:

```python
add_website_file("questions.txt")
```

The `--additional-paths` command line flag does the same job from
outside the code, repeated once per file (see
[Command line](../reference/cli.md)).
The helper `get_drafter_path("questions.txt")` resolves a name to
wherever the app's files actually live, which helps in the rare
case where plain `open` cannot find a file you bundled.

## Recipe: save and load your data

State lasts only as long as the browser tab stays open, and Drafter
has no built-in way to store it between visits. A visitor can still
keep their data by saving it as a file and loading that file the
next time. This recipe combines the two components above: a
`Download` writes the state out as text, and a `FileUpload` reads it
back in.

```python drafter height=360
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    entries: list[str]


def entries_to_text(entries: list[str]) -> str:
    text = ""
    for entry in entries:
        text = text + entry + "\n"
    return text


def text_to_entries(text: str) -> list[str]:
    entries = []
    for line in text.split("\n"):
        if line.strip() != "":
            entries.append(line.strip())
    return entries


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Journal"),
        BulletedList(state.entries),
        "New entry:",
        TextBox("entry"),
        Button("Record", "record"),
        "\n",
        Download("Save my journal", "journal.txt",
                 entries_to_text(state.entries).encode("utf-8")),
        " or ",
        Link("load a saved journal", "ask_for_file")
    ])


@route
def record(state: State, entry: str) -> Page:
    state.entries.append(entry)
    return index(state)


@route
def ask_for_file(state: State) -> Page:
    return Page(state, [
        "Choose the journal.txt file you saved earlier:",
        FileUpload("saved_file", accept=".txt"),
        "\n",
        Button("Load", "load_journal"),
        Link("Cancel", "index")
    ])


@route
def load_journal(state: State, saved_file: str) -> Page:
    if saved_file != "":
        state.entries = text_to_entries(saved_file)
    return index(state)


assert_equal(entries_to_text(["Day 1", "Day 2"]), "Day 1\nDay 2\n")
assert_equal(text_to_entries("Day 1\nDay 2\n"), ["Day 1", "Day 2"])
assert_state(load_journal(State(["Old entry"]), "Day 1\nDay 2\n"),
             State(["Day 1", "Day 2"]))
assert_state(load_journal(State(["Old entry"]), ""), State(["Old entry"]))

start_server(State(["Day 1: Captain ignored me."]))
```

Two helper functions do the converting. The `entries_to_text`
function turns the list in state into one string with an entry on
each line, and `text_to_entries` turns that string back into a list.
The first two tests check each direction.

The `Download` receives the text converted to bytes with
`.encode("utf-8")`. A download built from bytes saves every character
exactly as written. A download built from a plain string can lose
part of the text when it contains a `#` character, which matters when
the file holds whatever a visitor typed.

The `load_journal` route checks for an empty string before it
replaces anything. When the visitor presses Load without choosing a
file, `saved_file` arrives as `""`, and the check keeps the journal
they already have.

A journal is a list of strings, so one line per entry is enough. For
a state with several fields, decide on a fixed layout, such as one
field per line or one item per line with its parts separated by
commas, and write the two converting functions to match each other.
Test them the way this recipe does, because a saved file is only
useful if loading it gives back the same state.

## Recipe: split your program across files

When one file grows hard to find your way around, move helper
functions into a second file and import them. Put the second file in
the same folder as your main program. Here it is named
`pet_helpers.py`:

```python
def describe_mood(hunger: int) -> str:
    if hunger > 5:
        return "hungry"
    return "content"
```

The main program imports the function by the file's name, without
the `.py` ending:

```python
from drafter import *
from dataclasses import dataclass
from pet_helpers import describe_mood


@dataclass
class State:
    hunger: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Ada is " + describe_mood(state.hunger) + ".\n"
    ])


start_server(State(7))
```

While the program runs, Drafter watches both files, so saving either
one reloads the site. Three guidelines keep a project with several
files manageable:

- Keep `start_server(...)`, your `State` dataclass, and your routes
  in the main file. Move out the functions that do not use Drafter
  at all, such as calculations, text formatting, and lists of data.
  A helper file should not import from the main file, because two
  files that import each other usually fail to load.
- Give the helper file a specific name of your own. A name such as
  `helpers.py` is also the name of a public library. If your file
  is ever missing from the deployed site, the browser installs that
  library in its place, and the import error that follows is
  confusing to read.
- When you deploy, upload every `.py` file to the repository, next
  to `main.py`. The template from
  [Publish on GitHub Pages](../your-project/deploy/github-pages.md)
  includes them in the site. If you build the site another way,
  declare each one, as in `add_website_file("pet_helpers.py")`.

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
- **The deployed site reports an import error for your own file**:
  the helper file is not in the repository next to `main.py`, or its
  name is spelled differently from the `import` line. Upload it and
  run the deploy workflow again.
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
