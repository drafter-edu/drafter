---
page_type: lesson
title: First day with Drafter
audience: T
priority: P2
prereqs: []
symbols: []
outcome: Run the first Drafter class session.
search:
  exclude: true
---

# First day with Drafter

## Session goal

Every student leaves having run a working web app, changed it,
broken it, and fixed it. The session sells the payoff (a real
website, from Python they can read) and installs the
edit-save-reload loop as a habit. Vocabulary is deliberately
deferred; today produces the experiences the vocabulary will
later name.

## Audience and timing

Intro students about one-third through the course, comfortable
enough with functions to read a small program. One 50 minute
session; the 75 minute variant adds the second guided change and
a longer free-play block.

## Prerequisites

Students can write and call functions and have seen a dataclass
at least once. Drafter is installed, or the first ten minutes
absorb [installation](../../start/install.md).

## Materials

- [Build your first app](../../start/first-app.md): the counter
  tutorial the session shadows, and the students' reference
  afterward.
- [Make one visible change](../../start/make-a-change.md): the
  break-and-fix moves, scripted.
- A projector showing your editor and browser side by side.

## Plan

- **Hook (5 min).** Open a deployed Drafter app (yours, or a
  [gallery](../../your-project/gallery/index.md) project) on the
  projector, on a phone if you can. The pitch is one sentence:
  by the end of the course, you build one of these, and today
  you build your first one.
- **Demo (10 min).** Live-code the counter from
  [first-app](../../start/first-app.md), narrating as behavior,
  not vocabulary: "this function builds the page", "this button
  calls that function". Save, reload, click, twice.
- **Guided build (15 min).** Students type the counter
  themselves from the tutorial page. Resist distributing
  finished code; the typing is the point. Circulate for
  indentation accidents and missed saves.
- **Break it on purpose (10 min).** Everyone misspells their
  route name and reads the friendly error out loud, then fixes
  it. Errors just became a normal, survivable part of the loop,
  which is the most valuable ten minutes of the day.
- **Make it yours (8 min).** One visible change of their
  choosing: the text, a second button, a bigger step. Volunteers
  show the room.
- **Wrap (2 min).** Name exactly two things: the file runs on
  your machine and in the browser, and everything else waits.
  Point at [Start](../../start/index.md) as the path to
  continue alone.

## Checks for understanding

- "What happens the moment you save the file?" (The app
  reloads; no restart ritual.)
- "Point at the function that built the page you are looking
  at." (They can, by the demo's end.)
- "Your neighbor's app says the count is 7 and yours says 3.
  Why?" (Each program runs its own copy; a first seed for the
  [private-copy misconception](../student-misconceptions.md)
  before it forms.)

## Common stumbles

- Editing without saving, then despairing; the reload loop makes
  saving visible, so demonstrate the failure once on the
  projector.
- Route name and button target drifting apart during free play;
  the friendly error names both ends, so teach reading it rather
  than preventing it.
- A student races ahead into styling; fine, the
  [theme catalog](../../reference/themes.md) absorbs any amount
  of enthusiasm harmlessly.

## Extensions

Fast finishers apply a theme
(`set_website_style("retro")`), add a decrement button, or start
[the virtual pet](../../tutorials/virtual-pet.md), which is also
the assigned follow-on.

## Assessment ideas

Ungraded exit ticket: a screenshot of their modified counter
plus one sentence on what they changed. It confirms the loop
worked on their machine, which is the only outcome today needs
to certify.
