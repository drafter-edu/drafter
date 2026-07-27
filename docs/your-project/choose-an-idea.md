---
page_type: how-to
title: Choose a manageable idea
level: L2
audience: S
priority: P1
prereqs: [your-project]
symbols: []
outcome: Pick a project that fits the timeline and your skills.
---

# Choose a manageable idea

## Goal

You want a project that is genuinely yours *and* finishable in the
time you have. Those pull in opposite directions; this page is how
you get both.

## Before you start

The trick is to separate **shape** from **topic**. The shapes below
are proven: each one is buildable with what the guided projects
taught, and each has a known trap. The topic is where your project
becomes yours: a quiz *about your hometown*, a tracker *for your
climbing progress*, a store *for your imaginary bakery*. Choose a
shape from this page, then make the topic personal.

A good one-sentence test: "It's a ___ where the user ___ and the
app ___." When you can fill that in, you have an idea.

## The eight shapes

### Quiz game

A list of questions drives ask-answer-score, exactly like
[guided project 3](../tutorials/quiz-game.md).

- **Pages**: welcome, question, feedback, results.
- **State**: `questions: list[Question]`, `position: int`,
  `score: int`.
- **Milestones**: one hard-coded question answerable; questions
  from the list; scoring; results page.
- **Stretch**: categories ([SelectBox](../add/ask-for-information.md)),
  review of missed questions, per-question images
  ([Use pictures](../add/pictures.md)).
- **Watch out for**: writing twenty questions before one route
  works. Three questions until the app is done, then write content.

### Tracker or log

The user records things (workouts, books, meals, moods) and the
app shows totals and history.

- **Pages**: dashboard, add-entry form, full history.
- **State**: `entries: list[Entry]` where `Entry` has a few typed
  fields.
- **Milestones**: add an entry and see it listed; dashboard shows a
  count or total; a [Table](../add/show-a-collection.md) history;
  delete an entry.
- **Stretch**: filter by category, a
  [ProgressBar](../reference/components/data/progressbar.md) toward
  a goal, download the log ([files](../add/files.md)).
- **Watch out for**: dashboard math scattered through routes; put
  totals in helper functions where tests can reach them.

### Store or ordering app

Items with prices; the user browses, chooses, and checks out,
cousin of the [shop example](../examples/shop.md).

- **Pages**: storefront, item detail, cart, receipt.
- **State**: `items: list[Item]`, `cart: list[str]`,
  `money: int` (or a running total).
- **Milestones**: storefront lists items; buy one thing; the cart
  page; the receipt.
- **Stretch**: quantities, sales, out-of-stock handling.
- **Watch out for**: money as floats; keep prices in whole cents
  (`int`) and format only for display.

### Branching story

Scenes with choices; the reader's picks steer the path, the
narrative cousin of the quiz.

- **Pages**: one scene route driven by data, an ending page.
- **State**: `scenes: list[Scene]`, `current: str`, maybe
  `inventory: list[str]`.
- **Milestones**: two scenes connected; scenes fully data-driven;
  an ending that reflects choices.
- **Stretch**: items picked up along the way changing later scenes;
  pictures per scene.
- **Watch out for**: plot sprawl. Sketch the scene map on paper
  first and keep it under a dozen scenes.

### Converter or calculator tool

A focused tool: unit converter, grade calculator, recipe scaler,
tip splitter. The [calculator example](../examples/calculator.md)
is the seed.

- **Pages**: the tool, maybe a history page.
- **State**: the current inputs and results; possibly
  `history: list[str]`.
- **Milestones**: one conversion works; handles bad input politely;
  history.
- **Stretch**: several conversion modes via
  [RadioButtonGroup](../reference/components/input/radiobuttongroup.md),
  live results with [on_input](../add/live-behavior.md).
- **Watch out for**: this shape is the smallest, so courses often
  expect more polish; budget the saved time for design and tests.

### Flashcard deck

Cards with fronts and backs; flip, then self-grade, and the deck
decides what to show next.

- **Pages**: deck overview, study (front), study (back), done.
- **State**: `cards: list[Card]`, `position: int`,
  `right: int`, `wrong: int`.
- **Milestones**: flip one card; walk the deck; self-grading tally;
  missed cards come back around.
- **Stretch**: multiple decks, add-a-card form, shuffle.
- **Watch out for**: "shuffle" tempts `import random`, which works,
  but makes tests trickier; test the deck logic with a fixed order.

### Picture showcase

A gallery the user curates: upload, caption, browse, built on
[Use pictures](../add/pictures.md).

- **Pages**: gallery grid, single-picture view, upload form.
- **State**: `photos: list[Photo]` where `Photo` pairs a `Picture`
  with a caption.
- **Milestones**: one hard-coded picture shows; upload works;
  captions; the single-picture page.
- **Stretch**: transformations (rotate, grayscale), a
  [Download](../add/files.md) button per picture.
- **Watch out for**: nothing survives reload, so demo-day needs a
  few built-in starter pictures, not just uploads.

### Timed game

A game where time matters: speed quiz, reaction test, cookie-clicker
with decay, built on [Timers](../add/timers.md).

- **Pages**: menu, play, game over.
- **State**: the game numbers plus `seconds_left: int`.
- **Milestones**: the game works untimed; the countdown; game over
  at zero; a high score.
- **Stretch**: difficulty levels, pause.
- **Watch out for**: this is the only shape needing an L4 feature
  (timers). Build the untimed version completely first, so the
  timer is a garnish rather than a foundation.

## Out of scope, on purpose

Some tempting features do not fit a Drafter course project, for
reasons the [runtime model](../concepts/how-the-web-works.md)
explains: real accounts and passwords (nothing in the browser is
secret), live multiplayer or chat (each visitor runs their own
copy), and big datasets (state lives in one tab's memory). If your
dream project needs one of these, keep the dream, ship the
single-player simulation of it, and say so in your write-up; that
is what the [login example](../examples/login.md) does.

## Common problems

- **Two ideas, cannot choose**: pick the one whose *first
  milestone* you can picture building today.
- **The idea does not match any shape**: it probably matches one
  wearing a costume; find which shape has the same state. A "pet
  hotel manager" is a tracker; a "date-night picker" is a quiz or a
  converter.
- **The course gave you a spec**: the shapes still apply; find the
  one your spec resembles and steal its milestones and trap.

## You are ready for the next step when

You can say the one-liner out loud, name your shape, and name your
topic. Then go [sketch the pages](sketch-the-pages.md).
