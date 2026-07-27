---
page_type: how-to
title: Add features one at a time
level: L2
audience: S
priority: P2
prereqs: [your-project/build-one-path]
symbols: []
outcome: Grow the app without breaking it.
---

# Add features one at a time

## Goal

Your walking skeleton works, and your plan lists everything the
finished app should do. This page is about the order and rhythm
of getting from one to the other without ever breaking what you
have.

## Before you start

You have [one working path](build-one-path.md) and the
[test habit](test-as-you-go.md) started. You also have your
archetype's milestone list from
[choosing an idea](choose-an-idea.md); that list is your feature
queue.

## The rhythm

One feature at a time, each taken through the same four beats:

1. **Say it in a sentence.** "The visitor can remove an entry."
   If you cannot state the feature in one sentence, it is two
   features; split it.
2. **Find the recipe.** [Add to Your App](../add/index.md) is
   organized as a menu for exactly this moment. Removing items is
   on [Show a collection](../add/show-a-collection.md), a second
   page is on [Add and connect pages](../add/pages.md), and so
   on. Copy the shape, then adapt the names to your app.
3. **Build it until the app runs again.** Work in small saves;
   the reload loop tells you immediately when something is off.
4. **Test it and stop.** One assertion for the feature, a green
   Tests tab, and then you stop. The next feature starts from a
   working app, which is the entire trick.

The order that tends to work: finish the features your milestone
list calls required before touching anything decorative, and
within the required set, do the ones other features depend on
first (you cannot show a history page before anything saves
history).

## Keep routes small while you grow

Growth is where routes quietly rot. Two habits prevent it:

- **One responsibility per route.** A route that validates input,
  updates three fields, and builds two different page layouts is
  three functions wearing one name. When a route stops fitting on
  a screen, extract helper functions that return components or
  compute values.
- **Reuse page furniture.** The second time you write the same
  header block, move it into a helper function that both routes
  call. Shared furniture means a change happens once.

The [quiz game tutorial](../tutorials/quiz-game.md) models both
habits if you want to see them in a finished app.

## Resisting the shiny feature

Mid-project, a new idea will feel more interesting than the next
required milestone. Write the idea down in your planning notes,
then finish the milestone. The stretch features from your
archetype page are the sanctioned place for extra ambition, and
they are best started only after every required milestone works.
Scope grows by trades, not additions: if the new idea truly
matters, decide what it replaces.

## Common problems

- **The app has been broken for two days**: the feature was too
  big, and the skeleton habit slipped. Comment the half-feature
  out, get back to green, then reintroduce it in smaller pieces.
- **Two features tangled together**: build the data change first
  (state field plus route logic plus test), then the display that
  uses it. Splitting by layer usually untangles the knot.
- **Each feature makes the last one uglier**: routes are
  accumulating duplicated furniture. Pause for one extraction
  pass; growth gets cheaper immediately.
- **The feature needs something no recipe covers**: check the
  [component reference](../reference/components/index.md) before
  inventing machinery, and consider whether a nearby archetype's
  stretch feature is the same thing under a different name.

## You are ready for the next step when

Every required milestone from your plan works, each has its test,
and the Tests tab is green. Then give the app the polish pass it
has earned: [Improve the design](improve-the-design.md).
