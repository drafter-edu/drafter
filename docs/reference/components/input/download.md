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

A `Download` is a link that saves a file when clicked: contents
your app built, offered under a filename you choose. It is the only
way anything survives a visitor closing the tab, since
[state does not](../../../concepts/state.md).

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
- Downloads go to the visitor's device under their browser's rules
  (usually the downloads folder); your app never finds out whether
  they kept it.

## Accessibility

Say what the file is in the text ("Save the notes"), not "click
here"; download links surprise people, so the label should promise
one.

## Related components

- [FileUpload](fileupload.md): the door in.
- [Picture](../../data-types/picture.md): images as downloadable
  values.

## External links

- [The download attribute on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a#download)
