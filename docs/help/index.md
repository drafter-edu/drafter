---
page_type: index
title: Help
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Choose the right help path.
---

# Help

When something goes wrong, start from what you can see:

- **You have an error message.** Look it up in the
  [error index](errors/index.md), which is organized by the words in
  the message.
- **No error, but the app behaves wrongly.** Go to
  [Troubleshooting](troubleshooting.md), which is organized by
  symptom: blank page, button does nothing, changes not appearing.
- **You want to see what your app is doing.** The
  [debug panel guide](debug-panel.md) covers the state viewer,
  history, and tests;
  [Print and the console](printing-and-console.md) covers `print()`
  and the REPL.
- **You think Drafter itself is broken.** See
  [Report a Drafter bug](bug-reports.md), including the Download Bug
  Report button and what makes a report useful.

## Reading an error page

Drafter's error pages have two layers: a plain-language explanation
of what went wrong and what to try, and, below it, the technical
message and traceback. Read the friendly part first; it usually names
the route and the fix. The technical part matters when you ask for
help, so copy it whole rather than paraphrasing.

## Asking a good question

When you ask a person for help (an instructor, a TA, a forum), bring
three things:

1. What you expected to happen, and what happened instead.
2. The exact error text, copied, not retyped from memory.
3. The smallest piece of code that shows the problem.

The debug panel's bug-report download bundles most of this
automatically. Even when your problem is a homework question rather
than a Drafter bug, the bundle gives a helper most of what they
need.

## The five-minute checklist

Before you settle in for any deep debugging, run through the
classic checks:

- Did you save the file? Is the running app actually the saved
  version?
- Is there an error message in the terminal you started from, or in
  the debug panel?
- Does the app still break after a restart?
- Did it ever work? What changed since?
