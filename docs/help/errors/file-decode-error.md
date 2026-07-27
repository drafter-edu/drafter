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

A route parameter annotated `str` tells Drafter to treat the upload
as text, and the uploaded file was not text. Images, PDFs,
spreadsheets, and zip files are binary data that cannot be decoded
as text. The route did not run.

## Where to look

Look at the route receiving the upload, and at the filename in the
message, which usually reveals the problem (a `.jpg` file is never
text).

## Check

- **The visitor picked the wrong file**: your app expected text and
  they chose a photo. The `accept` filter narrows the picker:
  `FileUpload("notes", accept=".txt")`.
- **Your app actually wants binary files**: then the annotation is
  the problem, not the file.
- **A text file in a strange encoding**: this is rare, but a file
  saved in a non-UTF-8 encoding decodes wrongly or not at all.
  Annotating the parameter as `bytes` and decoding it yourself
  handles this case.

## Fix

Pick the annotation that matches the app's intent:

```python
@route
def receive(state: State, upload: bytes) -> Page:
    ...
```

A `bytes` parameter accepts any file, a `Picture` parameter decodes
images, and the
[file types](../../reference/data-types/file-types.md) carry the
contents along with the filename. Keep `str` only when the app
genuinely wants text, and pair it with an `accept` filter so wrong
files are hard to choose.

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
