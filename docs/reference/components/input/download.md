---
page_type: component
title: Download
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Download
outcome: Let the user save a file.
---

# Download

Group: [Input](../index.md#input)

## Description

A `Download` is a link that saves a file to the visitor's device
when clicked. Your app builds the file's contents and chooses the
filename it is saved under. Because
[state does not survive closing the tab](../../../concepts/state.md),
a downloaded file is the only way for information from your app to
outlast the visit.

## Syntax

```python
Download(text, filename, contents)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `text` | `str` | required | The visible link text. |
| `filename` | `str` | required | The name the saved file gets, extension included. |
| `contents` | `str`, `bytes`, or `Picture` | required | What goes in the file. |
| `content_type` | `str` | `"text/plain"` | The file's MIME type, when it matters. |

## Examples

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    lines: list[str]


@route
def index(state: State) -> Page:
    transcript = ""
    for line in state.lines:
        transcript = transcript + line + "\n"
    return Page(state, [
        Header("Meeting Notes"),
        BulletedList(state.lines),
        "Add a note:",
        TextBox("note"),
        "\n",
        Button("Note it", "note_it"),
        "\n",
        Download("Save the notes", "notes.txt", transcript)
    ])


@route
def note_it(state: State, note: str) -> Page:
    state.lines.append(note)
    return index(state)


start_server(State(["Meeting began late."]))
```

## Notes

- Build the contents fresh in the route each render, as above, so
  the download always matches the current state.
- The extension should match the contents: `.txt` for text, `.png`
  for a `Picture`, `.csv` for comma-separated rows.
- The visitor's browser decides where downloads are saved (usually
  the downloads folder); your app is not told whether the visitor
  kept the file.

## Accessibility

Make the link text say what the file is ("Save the notes"), not
"click here". An unexpected download can surprise the visitor, so
the text should make clear that clicking saves a file.

## Related components

- [FileUpload](fileupload.md): receiving files from the visitor
  instead.
- [Picture](../../data-types/picture.md): images as downloadable
  values.

## External links

- [The download attribute on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a#download)
