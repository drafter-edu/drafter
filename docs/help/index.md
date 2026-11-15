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

- **You have an error page or an error message.** Look it up in the
  [error index](errors/index.md), which lists errors by the title on
  the error page and by the words in the message.
- **No error, but the app behaves wrongly.** Go to
  [Troubleshooting](troubleshooting.md), which is organized by
  symptom, such as a blank page, a button that does nothing, or
  changes that do not appear.
- **You want to see what your app is doing.** The
  [debug panel guide](debug-panel.md) covers the state viewer,
  history, and tests.
  [Print and the console](printing-and-console.md) covers `print()`
  and the Python prompt on the page.
- **You have a general question.** The [FAQ](faq.md) gives short
  answers to the questions students ask most often, each with a link
  to the page that explains the answer in full.
- **You think Drafter itself is broken.** See
  [Report a Drafter bug](bug-reports.md), which covers the Download
  Bug Report button and what makes a report useful.

## Reading an error page

Every Drafter error page has the same parts, in the same order from
top to bottom.

1. The **title**, in large letters, names the kind of problem.
   One example is "Route Did Not Return a Page".
2. A **sentence or two in plain language** says what went wrong and
   usually names the route.
3. The **technical message**, in smaller type, starts with an error
   id such as `payload.verification_failed`, then a colon, then the
   exact message.
4. **What To Try Next** is a short list of fixes.
5. **Navigation Options** has four links, named Return to Index
   Page, Reset State and Return to Index, Reload Entire Application,
   and Submit a Bug Report.
6. **Technical Details** is a table that holds the error id, the
   route call that failed, the request, and the traceback when there
   is one.

Read the title and the sentence under it first. Next read "What To
Try Next", and after that the technical message. To find the help
page for an error, search the [error index](errors/index.md) for the
title. The technical message and the Technical Details table matter
when you ask someone for help, so copy them whole and do not
paraphrase them.

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

Before you settle in for any deep debugging, run through these five
checks.

- Did you save the file, and is the program still running? Saving
  reloads the site only while the program runs.
- Are you looking at the right browser tab? A tab that belongs to
  another program, or one showing a box titled "Disconnected", keeps
  showing an old version of a site until you reload it.
- Is there an error message in the terminal you started from, or
  under "Errors & Warnings" in the debug panel's Current tab?
- Does the app still break after you stop the program and run it
  again?
- Did it ever work? What changed since?
