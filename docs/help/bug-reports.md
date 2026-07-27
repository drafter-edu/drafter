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

Before you report anything, it is worth deciding which of two
situations you are in:

- **A Drafter bug** is Drafter doing something wrong or misleading:
  a crash inside Drafter's own code, an error message that pointed
  you the wrong way, a component rendering incorrectly, documented
  behavior not happening.
- **A homework question** is your app doing something you did not
  intend: a route that errors, a page that renders oddly because of
  its content, a test that fails. That deserves help too, from
  [Troubleshooting](troubleshooting.md), the
  [error index](errors/index.md), or your course staff, but if you
  file it as a bug report, it will likely be closed as a usage
  question.

A useful rule of thumb: if the fix would change *your* file, it is
a homework question, and if the fix would change *Drafter*, it is a
bug. When you genuinely cannot tell, ask your course staff first.
"Is this a bug?" is itself a perfectly good question to ask a
person.

## The Download Bug Report button

Drafter can gather the technical evidence for you. The same bundle
is available from two places:

- The debug panel's **Help menu**, via **Download Bug Report**.
- The built-in `--bug-report` page of any running Drafter app, which
  explains this same bug-vs-question distinction and offers the
  download button.

The bundle contains the technical record of your session: the
telemetry events (requests, responses, errors), system status, and
the context of the current page. It is downloaded as a file on your
computer, and you attach it wherever you report the bug. You are
welcome to open the file first to see what it records about your
session. It contains your code and your clicks, and that level of
detail is exactly what makes it useful to the people fixing the
bug.

## What a useful report says

Once the bundle is attached, a useful report needs only three more
sentences:

1. **What you did**: the click or code that triggers the problem,
   ideally as the smallest program that shows it.
2. **What you expected**: the behavior that the documentation, or
   common sense, led you to expect.
3. **What happened instead**: the exact error text or wrong
   behavior, copied rather than paraphrased.

Bugs that only happen sometimes are still worth reporting. Say how
often the problem appears, and attach the bundle from a session
where it happened.

## Where to send it

File reports on the
[Drafter issue tracker](https://github.com/drafter-edu/drafter/issues),
searching first to see whether your bug is already known (add your
bundle to the existing report if so). If your course has its own
reporting channel, use that instead; instructors collect the
reports they receive and forward the genuine bugs.

## Common problems

- **The download button did nothing**: the browser may have blocked
  the download, so check its download bar. If the download truly
  fails, screenshots of the debug panel's Log and Internals
  sections are a serviceable substitute.
- **The bug will not reproduce**: report it anyway with the bundle
  from the session where it happened; the telemetry often contains
  the sequence even when you cannot repeat it.
- **It turned out to be your own code**: that happens to everyone,
  and the distinction is genuinely hard to see from the inside.
  Even a report that gets closed as "not a bug" can lead to a
  better error message, so mention which part of the message
  confused you.

## Next steps

If what you actually need is help with your own app, start at
[Help](index.md). If an error message brought you here, the
[error index](errors/index.md) is the quickest place to look it up.
