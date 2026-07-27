---
page_type: error
title: Uploaded file couldn't be read as text
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Fix an uploaded file that cannot be read as text.
error_text: "does not look like unicode (utf-8) text"
---

# Uploaded file couldn't be read as text

## The error

```text
The file 'photo.jpg' does not look like unicode (utf-8) text.
Perhaps the file is not the type you expected, or the parameter
type should be bytes instead?
```

## What it means

A route parameter annotated `str` promises "this upload will be
text", and the uploaded file was not: images, PDFs, spreadsheets,
and zip files are bytes that no text decoding can make sense of.
The route did not run.

## Where to look

The route receiving the upload, and the filename in the message,
which usually gives the game away (`.jpg` is never text).

## Check

- **The visitor picked the wrong file**: your app expected text and
  they chose a photo. The `accept` filter narrows the picker:
  `FileUpload("notes", accept=".txt")`.
- **Your app actually wants binary files**: then the annotation is
  the problem, not the file.
- **A text file in a strange encoding**: rare, but a file saved in
  a non-UTF-8 encoding decodes wrongly or not at all; `bytes` plus
  deliberate decoding handles it.

## Fix

Pick the annotation that matches the app's intent:

```python
@route
def receive(state: State, upload: bytes) -> Page:
    ...
```

`bytes` accepts anything; `Picture` decodes images; the
[file types](../../reference/data-types/file-types.md) carry
contents plus filename. Keep `str` only when the app genuinely
wants text, and pair it with an `accept` filter so wrong files are
hard to choose.

## Confirm

Upload the same file again; the route runs and the parameter holds
what you expected (print `type(upload)` if unsure).

## Prevent

Decide "text or bytes?" when you write the `FileUpload`, set
`accept` to match, and annotate accordingly. The
[upload how-to](../../add/files.md) has the full annotation table.

## Understand

[Upload and download files](../../add/files.md): how uploads become
parameter values.
