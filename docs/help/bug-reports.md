---
page_type: how-to
title: Report a Drafter bug
audience: S
priority: P1
prereqs: []
symbols: []
outcome: File a useful bug report.
---

# Report a Drafter bug

## Goal

You believe Drafter itself misbehaved, and you want to report it so
it gets fixed.

## Before you start

First, the distinction that saves everyone time:

- **A Drafter bug** is Drafter doing something wrong or misleading:
  a crash inside Drafter's own code, an error message that pointed
  you the wrong way, a component rendering incorrectly, documented
  behavior not happening.
- **A homework question** is your app doing something you did not
  intend: a route that errors, a page that renders oddly because of
  its content, a test that fails. That deserves help too, from
  [Troubleshooting](troubleshooting.md), the
  [error index](errors/index.md), or your course staff, but a bug
  report will boomerang back with "this is a usage question."

Honest rule of thumb: if the fix would change *your* file, it is a
homework question; if the fix would change *Drafter*, it is a bug.
When you genuinely cannot tell, err toward asking your course staff
first; "is this a bug?" is itself a fine question to ask a human.

## The Download Bug Report button

Drafter packages the evidence for you. Two places offer the same
bundle:

- The debug panel's **Help menu**, via **Download Bug Report**.
- The built-in `--bug-report` page of any running Drafter app, which
  explains this same bug-vs-question distinction and offers the
  download button.

The bundle contains the technical record of your session: the
telemetry events (requests, responses, errors), system status, and
the context of the current page. It is a file on your computer; you
attach it wherever you report, and you can open it yourself first
to see what it says about you (it contains your code and your
clicks, which is exactly what makes it useful).

## What a useful report says

With the bundle attached, three sentences finish the job:

1. **What you did**: the click or code that triggers it, ideally as
   the smallest program that shows the problem.
2. **What you expected**: the behavior the docs or common sense
   promised.
3. **What happened instead**: the exact error text or wrong
   behavior, copied rather than paraphrased.

"Sometimes" bugs are still reportable; say how often and attach the
bundle from a session where it happened.

## Where to send it

File reports on the
[Drafter issue tracker](https://github.com/drafter-edu/drafter/issues),
searching first to see whether your bug is already known (add your
bundle to the existing report if so). If your course has its own
reporting channel, prefer it; instructors batch and forward real
bugs.

## Common problems

- **The download button did nothing**: the browser may have blocked
  the download; check its download bar. Failing that, screenshots of
  the debug panel's Log and Internals sections are a serviceable
  substitute.
- **The bug will not reproduce**: report it anyway with the bundle
  from the session where it happened; the telemetry often contains
  the sequence even when you cannot repeat it.
- **It turned out to be your own code**: no shame in it; the
  distinction is genuinely blurry from the inside, and a closed
  "not a bug" report still improves the error message that confused
  you, so mention what you misread.

## Next steps

If what you actually need is help with your own app, start at
[Help](index.md); if an error message brought you here, the
[error index](errors/index.md) is the fast path.
