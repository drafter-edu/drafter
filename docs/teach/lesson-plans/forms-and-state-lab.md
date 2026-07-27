---
page_type: lesson
title: Forms and state lab
audience: T
priority: P2
prereqs: []
symbols: []
outcome: Run a lab connecting forms to state.
search:
  exclude: true
---

# Forms and state lab

## Session goal

Students can build a form whose values reach a route, explain
the name-to-parameter contract in their own words, and store a
received value in state so a later page remembers it. Those are
[big ideas](../big-ideas.md) three, four, and five, and this lab
is where they usually click.

## Audience and timing

Students who finished the [virtual pet](../../tutorials/virtual-pet.md)
(buttons and state mutation, no forms yet). One 75 minute lab,
or 50 minutes ending before the challenge round.

## Prerequisites

A working counter-style app in every editor before the lab
starts, because the lab modifies a running app rather than
starting fresh. Students have seen `TextBox` in a demo but not
used it.

## Materials

- [Ask the user for information](../../add/ask-for-information.md):
  the recipe page the lab follows.
- [Forms and input](../../concepts/forms-and-input.md): the
  concept page, assigned after (not before) the lab.
- [Build a story maker](../../tutorials/story-maker.md): the
  tutorial this lab rehearses for.
- A projected "contract diagram": `TextBox("color")` on one
  side, `def paint(state, color: str)` on the other, one arrow.

## Plan

- **Warmup prediction (10 min).** Project a two-route app with
  one TextBox and ask, before running it: where does the typed
  value go? Collect three predictions, then run it. The arrow
  diagram goes up and stays up all session.
- **Checkpoint 1: one field (15 min).** Students add a TextBox
  and a receiving route to their own app; the value appears on
  the response page. The moment of stuckness is nearly always a
  name mismatch, which is the contract teaching itself; direct
  the stuck to the error message before you rescue them.
- **Checkpoint 2: remember it (15 min).** The received value
  moves into a state field and shows on the index page too.
  This distinguishes "the route saw it" from "the app remembers
  it", the difference that matters.
- **Checkpoint 3: convert it (15 min).** A numeric field (an
  age, a quantity) gets an `int` annotation, and students
  predict what typing "seven" does before trying it. The
  friendly conversion error becomes a feature: annotations are
  load-bearing.
- **Challenge round (15 min).** Two fields, one route, both
  remembered; fastest pairs add a `SelectBox`. The
  [recipe page](../../add/ask-for-information.md) is officially
  open season; using docs mid-build is a habit worth grading
  into existence.
- **Wrap (5 min).** A student states the contract in their own
  words; you write it verbatim on the board next to the diagram
  and assign the [concept page](../../concepts/forms-and-input.md)
  as the naming of what they just did.

## Checks for understanding

- "The box is named `color` and the parameter is named `colour`.
  What exactly happens?" (A friendly missing-parameter error,
  and they should be able to say which name to change.)
- "Why did `state.favorite = color` need to happen inside the
  route?" (State changes when routes change it; nothing is
  remembered by accident.)
- "What does the `int` in `amount: int` actually do?" (Converts
  the arriving text, and stops politely when it cannot.)

## Common stumbles

- Name mismatches, the lab's featured attraction; the
  [missing parameter entry](../../help/errors/missing-parameter.md)
  is the page to have open.
- Expecting the TextBox to remember its own contents; the
  pre-filling pattern (`TextBox("color", state.favorite)`)
  earns a projected moment in checkpoint 2.
- Submitting via a Link instead of a Button and wondering where
  the values went; only a Button submits the form.

## Extensions

A `CheckBox` with a `bool` parameter; a two-page wizard where
page two's form pre-fills from page one's answers; a
"[mad-lib](../../tutorials/story-maker.md) head start" for pairs
who finish everything.

## Assessment ideas

The checkpoint app itself, submitted with one
`assert_state` test on the receiving route. A short follow-up
quiz item shows a TextBox/route pair with a mismatch and asks
what the visitor sees, which tests the contract without a
computer.
