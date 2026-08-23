---
page_type: index
title: Error index
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Find an entry from exact error text.
---

# Error index

Find your error by the words in the message. Use your browser's
find-in-page (++ctrl+f++) or the site search with a distinctive phrase
from the error, in quotes.

## By message text

| The message contains | Go to |
| -------------------- | ----- |
| `points to non-existent page` | [Link or button points to an unknown route](route-not-found.md) |
| `expects a value for parameter ... but none was provided` | [Route is missing a parameter a form expected](missing-parameter.md) |
| `expects int but got` | [Could not convert text to an int](type-conversion-int.md) |
| `expects float but got`, or another type | [Could not convert a value to the parameter's type](type-conversion-other.md) |
| `type changed from ... to ...` | [State doesn't match the State class](state-mismatch.md) |
| `must be a list of strings, numbers, booleans, or components` | [Page content must be a list of strings, numbers, booleans, or components](page-content-invalid.md) |
| Two components share a `name` | [Two components share a name](duplicate-component-name.md) |
| SelectBox default not among the options | [SelectBox default not in options](selectbox-default-missing.md) |
| `Header level must be between 1 and 6` | [Header level must be 1-6](header-level-invalid.md) |
| `Circular Reference` in a generated test | [Circular Reference appears in generated tests](circular-reference-tests.md) |
| A file `does not look like unicode (utf-8) text` | [Uploaded file couldn't be read as text](file-decode-error.md) |
| `404` for an image or file on the deployed site | [Image or file works locally but 404s when deployed](missing-asset-on-deploy.md) |
| A red X on your GitHub deployment | [GitHub Actions build failed](deploy-build-failed.md) |
| An `import` fails in the browser | [A library import fails in the browser](package-import-error.md) |
| Camera, microphone, or location `permission denied` | [Device permission denied](permission-denied-device.md) |

## Not an error, but broken anyway

- If code placed after `start_server()` never runs, nothing is wrong:
  [that is how start_server works](nothing-after-start-server.md).
- If there is no error message but the app behaves incorrectly, see
  [Troubleshooting](../troubleshooting.md), which is organized by symptom.

## Python's own errors

`SyntaxError`, `NameError`, `TypeError`, `IndexError`, and similar
messages come from Python itself, not from Drafter. Drafter's error
page explains the common ones in plain language above the traceback.
Read that friendly explanation first, then go to the line it names.
The habits in
[Reading an error page](../index.md#reading-an-error-page) apply
here as well.

## How these pages work

Every entry follows the same eight steps: the error verbatim, what it
means, where to look, how to check which cause you have, the fix, how
to confirm, how to prevent it, and a link to the concept page that
addresses the underlying misunderstanding. If your error is not
listed and the friendly message does not resolve the problem,
consider a [bug report](../bug-reports.md); this index grows from
the errors students actually encounter.
