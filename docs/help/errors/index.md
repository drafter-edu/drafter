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

A Drafter error page starts with a title in large letters, followed
by a sentence that describes the problem and then a technical
message. Look at the title first and find it in the first table
below. Some titles cover several different problems, and for those
the table also gives a phrase to look for in the message. If your
problem has no title, or the title is not listed, use the second
table, which is organized by the words in the message.

You can also search for either one. Use your browser's find-in-page
(++ctrl+f++) or the site search with the title, or with a distinctive
phrase from the message, in quotes.

## By the title on the error page

| The title | The message contains | Go to |
| --------- | -------------------- | ----- |
| `Route Did Not Return a Page` | Any message | [Route did not return a Page](route-did-not-return-a-page.md) |
| `State Changed Type` | Any message | [State doesn't match the State class](state-mismatch.md) |
| `Components Share a Name` | Any message | [Two components share a name](duplicate-component-name.md) |
| `Problem With the Route's Arguments` | `expects a value for parameter ... but none was provided` | [Route is missing a parameter a form expected](missing-parameter.md) |
| `Problem With the Route's Arguments` | `expects int but got` | [Could not convert text to an int](type-conversion-int.md) |
| `Problem With the Route's Arguments` | `expects float but got`, or another type | [Could not convert a value to the parameter's type](type-conversion-other.md) |
| `Problem With the Route's Arguments` | `does not look like unicode (utf-8) text` | [Uploaded file couldn't be read as text](file-decode-error.md) |
| `Problem With the Route's Arguments` | `but no value was provided by` | [Blank values](../../reference/route.md#blank-values) |
| `Button Points to a Missing Page`, or `Link Points to a Missing Page` | Any message | [Link or button points to an unknown route](route-not-found.md) |
| `Page Content Problem` | Any message | [Page content must be a list of strings, numbers, booleans, or components](page-content-invalid.md) |
| `SelectBox Default Is Not an Option` | Any message | [SelectBox default not in options](selectbox-default-missing.md) |
| `Header Level Out of Range` | Any message | [Header level must be 1-6](header-level-invalid.md) |
| `Page Not Found` | `No route found for URL` | [Link or button points to an unknown route](route-not-found.md) |
| `Module Not Found` | `No module named` | [A library import fails in the browser](package-import-error.md) |
| `File Not Found` | `File not found`, on the deployed site only | [Image or file works locally but 404s when deployed](missing-asset-on-deploy.md) |
| `Unknown Name`, `Type Mismatch`, `Unusable Value`, `Missing Attribute`, `List Position Out of Range`, `Missing Dictionary Key`, `Division by Zero`, `Endless Recursion`, or `Problem Loading This Page` | A message from Python | [Python's own errors](#pythons-own-errors) |
| `Error`, on a dialog that says "Error running student code" | `ModuleNotFoundError` | [A library import fails in the browser](package-import-error.md) |
| `Website File Not Found`, or `Website File Name Has Different Capital Letters`, printed in the terminal | Any message | [add_website_file](../../reference/site-config.md#add_website_file) |

## By message text

| The message contains | Go to |
| -------------------- | ----- |
| `finished without returning a Page`, or `did not return a Page() object` | [Route did not return a Page](route-did-not-return-a-page.md) |
| `points to non-existent page` | [Link or button points to an unknown route](route-not-found.md) |
| `expects a value for parameter ... but none was provided` | [Route is missing a parameter a form expected](missing-parameter.md) |
| `was sent to ..., but the function has no matching parameter` (a warning in the debug panel) | [A form field with no matching parameter](missing-parameter.md#a-related-warning-a-form-field-with-no-matching-parameter) |
| `expects int but got` | [Could not convert text to an int](type-conversion-int.md) |
| `expects float but got`, or another type | [Could not convert a value to the parameter's type](type-conversion-other.md) |
| `expects ... but no value was provided by` | [Blank values](../../reference/route.md#blank-values) |
| `has a state that is a ..., but the previous state was a ...` | [State doesn't match the State class](state-mismatch.md) |
| `changed the site state from ... to ...` (a warning in the debug panel) | [A warning about the state's type](state-mismatch.md#a-warning-about-the-states-type) |
| `must be a list of strings, numbers, booleans, or components`, `must be given as one list`, or `Unsupported page content type` | [Page content must be a list of strings, numbers, booleans, or components](page-content-invalid.md) |
| `has multiple components with the same name` | [Two components share a name](duplicate-component-name.md) |
| `default_value ... is not in options` | [SelectBox default not in options](selectbox-default-missing.md) |
| `Header level must be between 1 and 6` | [Header level must be 1-6](header-level-invalid.md) |
| `Circular Reference` in a generated test | [Circular Reference appears in generated tests](circular-reference-tests.md) |
| A file `does not look like unicode (utf-8) text` | [Uploaded file couldn't be read as text](file-decode-error.md) |
| `404` for an image or file on the deployed site | [Image or file works locally but 404s when deployed](missing-asset-on-deploy.md) |
| A red X on your GitHub deployment | [GitHub Actions build failed](deploy-build-failed.md) |
| `ModuleNotFoundError`, or `No module named` | [A library import fails in the browser](package-import-error.md) |
| `Camera access denied`, `Microphone access denied`, or `Location access denied` | [Device permission denied](permission-denied-device.md) |
| `The address of this page named a route that needs values from a form or a button` (a warning in the debug panel) | [Reloading the tab shows a page I did not expect](../troubleshooting.md#reloading-the-tab-shows-a-page-i-did-not-expect) |
| `The browser could not load one of the images` (a warning in the debug panel) | [A picture shows as a broken image](../troubleshooting.md#a-picture-shows-as-a-broken-image) |
| `has code after start_server(...)` in the terminal, or `comes after start_server(...)` (a warning in the debug panel) | [Code after start_server() never runs](nothing-after-start-server.md) |
| `Unknown start_server option` in the terminal, or `start_server was given an option named` (a warning in the debug panel) | [start_server](../../reference/start-server.md#student-relevant-options) |

## Not an error, but broken anyway

- If code placed after `start_server()` does not seem to run, see
  [Code after start_server() never runs](nothing-after-start-server.md).
- If reloading the browser tab shows the first page in place of the
  page you were on, see
  [Reloading the tab shows a page I did not expect](../troubleshooting.md#reloading-the-tab-shows-a-page-i-did-not-expect).
- If there is no error message but the app behaves incorrectly, see
  [Troubleshooting](../troubleshooting.md), which is organized by symptom.

## Python's own errors

`NameError`, `TypeError`, `IndexError`, and similar messages come
from Python itself, not from Drafter. When one of them happens while
a route runs, Drafter shows an error page with a plain-language title
such as "Unknown Name", "Type Mismatch", or "List Position Out of
Range", and a sentence that explains the problem above the traceback.
A `ValueError` appears as "Unusable Value", and an error that has no
title of its own appears as "Problem Loading This Page". Read the
explanation first, then go to the line the traceback names. A `SyntaxError` in your file does not produce an error page.
The site keeps showing the last working version, and a dialog titled
"Syntax Error" names the line to fix. The habits in
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
