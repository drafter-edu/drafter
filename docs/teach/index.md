---
page_type: index
title: Teaching with Drafter
audience: T
priority: P1
prereqs: []
symbols: []
outcome: Orient instructors.
search:
  exclude: true
---

# Teaching with Drafter

This area is for instructors. If you are a student, you probably
want [Start](../start/index.md) or the
[Reference](../reference/index.md) instead.

Drafter was built for a specific teaching situation: an
introductory Python course, mostly non-majors, where students have
met functions, dataclasses, and lists, and want to build something
they can show other people. Everything in this section assumes
that situation, and notes where your course might differ.

## Where to go

- **[Why Drafter](why-drafter.md)**: the pedagogical case, the
  tradeoffs against Flask, Streamlit, and raw web development, and
  the honest limits. Read this first if you are deciding whether
  to adopt it.
- **[The big ideas](big-ideas.md)**: the concepts that carry the
  whole library, in the order we suggest teaching them.
- **[Beyond the student docs](beyond-the-basics.md)**: the
  advanced surface (events, live updates, media components,
  configuration, the command line) that the student journey
  deliberately keeps quiet about.
- **[Student misconceptions](student-misconceptions.md)**: the
  beliefs novices form about Drafter, what they look like in
  student code, and how to repair them.
- **[Expert misconceptions](expert-misconceptions.md)**: the
  wrong assumptions experienced web developers (and instructors)
  bring, mostly by analogy to Flask.
- **[Lesson plans](lesson-plans/index.md)**: three ready-to-run
  session plans (first day, forms and state, testing).
- **[Project ideas](project-ideas.md)**: sixteen assignable
  ideas rated by scope, plus the anti-patterns to redirect.

## How the student docs are organized

Students walk a journey: [Start](../start/index.md) (first
success), [Guided Projects](../tutorials/index.md) (four tutorials
that form the instructional spine), [Add to Your App](../add/index.md)
(task pages in learner language), and
[Your Project](../your-project/index.md) (the final-project arc,
ending in deployment). Concept pages exist but stay out of the
main navigation; students reach them through "Understand it"
links after they have already seen the behavior. Knowing this
shape helps you assign pages: point students at tasks
("add a form"), not at concepts ("read about state").

## Presenting a page in class

Every page of these docs can be shown as slides. The screen icon in
the header (its tooltip reads "Present this page as slides") opens
the page as a deck, starting at the section you are reading:

- Each `##` section becomes a slide, and a section too long for the
  screen continues on the next one. Demos stay live, so you can
  click and edit them in front of the room.
- ++arrow-right++, ++space++, or ++page-down++ moves forward, and
  ++arrow-left++ or ++page-up++ moves back. ++o++ lists the slides,
  ++f++ toggles full screen, and ++esc++ returns you to the page at
  the slide you stopped on.
- A program too long for the screen scrolls inside its own box; the
  forward key pages through it before moving to the next slide.
- The deck follows the window. Zoom the browser in for a large
  room, or go full screen, and the slides are laid out again to
  fit.
- The last slide of a page links to the next page and keeps slide
  mode on.
