---
page_type: lesson
title: Testing lab
audience: T
priority: P2
prereqs: []
symbols: []
outcome: Run a lab building the testing habit.
search:
  exclude: true
---

# Testing lab

## Session goal

Students internalize that routes are callable functions, write
one honest assertion per feature, and read a failing test as
information rather than as punishment. The lab's centerpiece is
diagnosing planted bugs with tests, which converts testing from
a chore into a power.

## Audience and timing

Students with a multi-page, form-using app of their own (after
the [story maker](../../tutorials/story-maker.md), ideally
during the [quiz game](../../tutorials/quiz-game.md)). One 50
minute session.

## Prerequisites

Comfort calling functions with made-up arguments, and a working
app in every editor. Students have seen `assert_state` in
tutorial code without necessarily writing one.

## Materials

- [Test a feature](../../add/test-a-feature.md): the reference
  recipe.
- A starter file you distribute: a small working app (a treat
  counter with a feed route and a reset route works well) with
  **three planted bugs**: one logic slip (`+ 2` instead of
  `+ 1`), one wrong page text, and one route that forgets to
  return `index(state)` and builds a slightly wrong page
  instead.
- The debug panel's Tests tab on the projector.

## Plan

- **The reveal (10 min).** Project a route, then call it in
  plain Python: `feed(State(0))`, no server, no browser. Let
  that sink in; routes were functions all along. Wrap the call
  in `assert_state(feed(State(0)), State(1))`, run, and show
  where the green result lands in the Tests tab.
- **Bug hunt (20 min).** Distribute the starter. The rule:
  every bug must be *convicted by a test before it is fixed*;
  a test that fails, then the fix, then the same test green.
  Pairs work well. The wrong-text bug forces `assert_has`, the
  logic bug `assert_state`, and the third teaches that tests
  catch what eyeballs skim past.
- **Your app, your tests (15 min).** Everyone writes two
  assertions for their own project: one `assert_state` on a
  logic route, one `assert_has` on a page. The
  [recipe page](../../add/test-a-feature.md) is open; you
  circulate for expected-values-copied-from-output, the
  anti-pattern worth catching live.
- **Wrap (5 min).** Name the habit (one feature, one test, same
  day) and where it lives in their project workflow
  ([Test as you go](../../your-project/test-as-you-go.md)).

## Checks for understanding

- "Why did `assert_state(feed(State(0)), State(1))` not need
  the server running?" (Routes are functions; the call is the
  test.)
- "Your test expected `State(2)` and got `State(2)` but still
  shows the page differing. Which assertion should this feature
  have used?" (Two assertions test two different things; state
  and page are separate claims.)
- "When is it fine for a test to fail?" (When the code is
  wrong, and when the *test* is stale after a deliberate
  change; both answers matter.)

## Common stumbles

- Producing expected values by running the code and copying its
  answer, which proves nothing; require hand-worked
  expectations in the bug hunt.
- Whole-page comparisons that shatter on any edit; steer to
  `assert_has` with one meaningful needle, and save page
  freezing for the [finishing tutorial](../../tutorials/finishing.md).
- Fear response to red output; the bug hunt's framing (a red
  test is a conviction, and you are the detective) is the
  antidote, so protect it in your language all session.

## Extensions

Test a failure path (the reset route on an already-zero state);
freeze one finished page via the History tab and read the
generated `assert_equal`; write a test *first* for the next
planned feature and watch it go green when the feature lands.

## Assessment ideas

Collect the convicted-and-fixed starter file: three failing
tests turned green tells the whole story. On the final project,
grade for one honest assertion per feature (the
[rubric notes](../classroom.md) suggest weightings), which makes
this session's habit worth points for the rest of the term.
