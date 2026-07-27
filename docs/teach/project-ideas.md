---
page_type: reference
title: Project ideas
audience: T
priority: P2
prereqs: []
symbols: []
outcome: Assign well-scoped projects.
search:
  exclude: true
---

# Project ideas

Sixteen assignable project ideas, rated by scope and tagged with
the concepts they exercise. They extend the eight student-facing
[archetypes](../your-project/choose-an-idea.md), which bound
structure while leaving topics open; the strongest assignments
name an archetype and let students choose the subject.

Scope ratings: **S** finishable in about a week alongside other
work; **M** a two-to-three week unit project; **L** a full final
project with milestones.

## The list

| Idea | Scope | Exercises | Notes |
| ---- | ----- | --------- | ----- |
| Personality quiz ("Which pet are you?") | S | forms, branching, score tallying | The gentlest complete app; results page varies by tallied answers. |
| Flashcard drill | S | lists of dataclasses, state, conditionals | Card list drives one route; wrong answers can requeue. |
| Unit converter suite | S | forms, type conversion, helper functions | Several converters behind one menu; annotations do real work. |
| Daily journal | S | TextArea, lists, empty states | Add-and-display with timestamps via the date inputs. |
| Trivia quiz with timer | M | quiz archetype plus Timer | The timer forces the persistent-component conversation. |
| Habit or workout tracker | M | nested dataclasses, tables, milestone checks | Rich state design; totals and streaks reward helper functions. |
| Restaurant or bake-sale ordering | M | store archetype, validation, running totals | Cart logic; the honest no-real-payments talk comes free. |
| Branching story with inventory | M | dynamic pages, Argument, state flags | The classic; inventory flags gate story branches. |
| Photo booth | M | Camera, Picture transforms, Download | Permission handling is part of the grade. |
| Study-spot (or anything) map | M | Map, markers, click routes | Needs network for tiles; data can be a curated list. |
| Pet simulator with mood chart | M | state, MatPlotLibPlot, Clock ticks | The chart redraw-from-state pattern, visibly. |
| Soundboard or tiny instrument | M | Tone, Melody, effects | High delight per line of code; scope-safe. |
| Text adventure with saved progress | L | branching story at full size | Needs a route map before code; enforce the sketch step. |
| Classroom review game | L | quiz plus timers plus scoreboard styling | A team mode must fake multiplayer honestly (pass-the-laptop). |
| Personal collection manager | L | tracker archetype at full size, files | Import/export via upload and download stretches the file types. |
| Choose-your-own study guide | L | dynamic pages, DefinitionList, Details | Students teach their own course topic; doubles as review. |

## Anti-patterns to redirect

These arrive every term, sound reasonable, and collide with the
[architecture](why-drafter.md):

- **Real accounts or login-protected content.** Everything ships
  to the browser; a login can gate the flow but protects
  nothing. Redirect to a login *simulation*, clearly labeled,
  which is genuinely good UX practice.
- **Anything multiplayer or shared** (chat, leaderboards,
  collaborative lists). Visitors never share state. Redirect to
  pass-the-device turn-taking, which preserves the game design
  work.
- **Data that must survive reload** (a diary that keeps entries
  forever). State is per-tab memory. Redirect to
  download-your-data as a feature, or reframe the app around a
  session.
- **Big datasets or live feeds.** CORS and page size both bite.
  Redirect to a curated slice bundled with the app.
- **"An app store's worth of features."** The
  [milestone structure](../your-project/choose-an-idea.md)
  is the cure; require the walking skeleton demo early.

## Making any idea gradeable

Whatever the idea, the same rubric skeleton fits: a working
deployed app (the [deploy guide](../your-project/deploy/index.md)
makes this fair to require), one test per feature, a state
design that matches the data, and an honest interface (labels,
empty states, no fake security).
