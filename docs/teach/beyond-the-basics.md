---
page_type: reference
title: Beyond the student docs
audience: T
priority: P1
prereqs: []
symbols: []
outcome: Know the advanced surface not obvious from student docs.
search:
  exclude: true
---

# Beyond the student docs

The student journey deliberately shows a narrow surface: pages,
forms, state, tests, styling, deployment. Drafter is larger than
that. This page maps the rest, so you know what exists when a
strong student outruns the spine or a project needs something
unusual.

## Live updates and partial pages

Routes normally return a whole `Page`, but three other payloads
exist ([Live updates](../concepts/live-updates.md) is the student
treatment):

- `Fragment` replaces one part of the page, targeted by id or
  class, without a full re-render.
- `Update` changes state silently, with no visual change.
- `Redirect` answers one route by sending the visitor to another.

Any component accepts event keywords (`on_click`, `on_input`,
`on_change`, and others) whose value is a route name; the route
runs when the event fires. This is enough to build live character
counters, autosave, and small games. Event payloads can carry
extra data (a Timer's `remaining`, a Map click's `latitude`) that
routes receive as named parameters.

## The specialized component families

All documented in the [component reference](../reference/components/index.md),
none required by the core journey:

- **Time**: `Timer` (countdown firing a route), `Clock` (repeating
  tick), both optionally `persistent` across re-renders.
- **Place**: `Map` (interactive Leaflet map with markers and click
  routes; needs network for imagery), `CurrentLocation` (browser
  geolocation with a permission workflow).
- **Capture**: `Camera` (webcam photos arriving as `Picture`
  values students can transform pixel by pixel).
- **Sound**: `Tone`, `Melody`, `Sound`, `Microphone`,
  `AudioRecorder`, and audio effects; a full web-audio family.
- **Media**: `MatPlotLibPlot` (matplotlib charts on pages),
  `Audio`, `Video`, `SVG`, `Canvas`.
- **Data display**: `ProgressBar`, `Meter`, semantic layout
  regions, definition lists.

The permission-based components (camera, location, microphone)
share a pattern worth teaching if you use any of them: the visitor
can always refuse, and the arriving value carries a `status` field
instead of raising an error.

## Persistent components

Components are normally rebuilt on every render. Passing
`persistent=True` (timers, clocks, maps, audio) keeps the live
component running across re-renders, and `RemovePersistent` evicts
one. This matters the moment a student builds a game loop.

## Configuration and site setup

The `set_website_*` family controls the site shell: title, theme,
framing, custom CSS and JS, and the `set_site_information` record
(author, description, planning documents) that powers the deployed
site's about page. The student docs cover these in
[Site configuration](../reference/site-config.md); the spread of
options is larger than the deploy guide lets on.

## The command line

`drafter file.py` runs an app; `drafter file.py --compile` builds
the deployable static site. Flags exist for port, host, theme,
production mode, and bundling extra files (`--additional-paths`).
Students meet only the minimum in the deploy guide.

## Runnable docs embedding

The documentation site's own runnable examples come from a MkDocs
plugin that compiles fenced code blocks into sandboxed Pyodide
iframes, sharing one runtime per page. If you write course
materials with MkDocs, the same plugin ships with Drafter; see
[Writing documentation](../dev/docs-guide.md).

## Deliberately not shown to students

Choices you should know are choices, so you do not undo them by
accident:

- **Dictionaries, sets, and most built-ins work fine in state.**
  The docs use lists of dataclasses everywhere because the
  audience has not learned dicts, not because Drafter cannot
  store them.
- **Exceptions are never required.** Failure states arrive as
  values (a `Location`'s `status`, a friendly error page), so
  `try`/`except` stays out of the course.
- **The internals have names students never hear**: the bridge,
  payload envelopes, the client server. The student-facing
  runtime model ([How Drafter works](../start/how-drafter-works.md))
  is simplified but never false; the full story is in the
  [developer docs](../dev/architecture.md).

## Related

- [Extend](../extend/index.md): the student-facing advanced area
  (Pyodide, packages, JavaScript interop, security).
- [Developer documentation](../dev/index.md): architecture and
  the full generated API reference.
