---
page_type: troubleshooting
title: Troubleshooting
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Diagnose problems by symptom.
---

# Troubleshooting

This page is organized by what you can see on the screen. If you
have an actual error message, the [error index](errors/index.md)
is a faster place to look.

## The page is blank

Usually the route ran but returned something empty, or never ran at
all.

- Check the terminal and the debug panel for an error that happened
  while the page was being built; an error can leave the old or empty
  page behind.
- Check that your `index` route returns a `Page` on every path. A
  route that ends without `return` returns `None`, and there is
  nothing to show.
- If the whole site is blank on first load, give it a moment: see
  "The first load is slow" below.

## A button does nothing

- Open the debug panel and click the button again: did a request
  happen? If yes, the route ran; check what it returned and whether
  it actually changed state.
- If the click produced an error page instead, read it; the two most
  common are a
  [missing parameter](errors/missing-parameter.md) and a
  [conversion failure](errors/type-conversion-int.md).
- Make sure the route mutates the state it was given rather than a
  fresh copy: `state.score = state.score + 1`, not
  `state = State(...)`.
- If the page never re-renders, the button appears to do nothing
  even when the route ran. The route should end by returning a page
  that shows the change, usually `return index(state)`.

## My changes are not appearing

Work through the classic save-and-reload steps, in order:

1. Save the file. Changes you have not saved never run.
2. If you ran the program yourself, stop it and run it again;
   the site is built from the code as it was when you started it.
   (The `drafter` command watches your file and restarts for you.)
3. Refresh the browser tab.
4. If a syntax error crept in, the old site keeps running while the
   terminal shows the error; fix it and save again.
5. If you edited a helper file (not your main program) and the
   terminal printed "Drafter noticed that ... is in a large or broad
   folder" at startup, only files your site has already used reload
   automatically. Move the project into its own small folder, or see
   [live reload](../reference/live-reload.md).

## The site will not start

- Read the terminal message. A syntax error names the file and line;
  fix it and rerun.
- If the message says the port is in use, another copy of your app is
  probably still running; stop it, or pass a different port with
  `start_server(port=8081)`.
- If `import drafter` itself fails, the installation is the problem;
  see [Get Drafter running](../start/install.md).

## My code after start_server never runs

That is [by design](errors/nothing-after-start-server.md):
`start_server(...)` takes over the program. Configuration and tests
go before it, and behavior goes in routes.

## The first load is slow

Behind the scenes, the browser downloads and starts a complete copy
of Python before your first page appears, so expect a delay of a
few seconds on the first visit. If the page never loads at all,
check the browser's network connection, and check whether the
terminal shows that the site actually started.

## Tests pass but the app misbehaves

Tests only exercise the routes you wrote them for, so the
misbehavior is probably on a path that has no test yet. Reproduce
the bad behavior by hand,
note which route ran, and write a failing assertion for it before
fixing it. See [Test a feature](../add/test-a-feature.md).

## Still stuck?

- [The debug panel in depth](debug-panel.md) shows your app's state
  and history while you interact with it.
- [Print and the console](printing-and-console.md) is the fastest way
  to see what a route actually received.
- If you believe Drafter itself misbehaved, see
  [Report a Drafter bug](bug-reports.md).
