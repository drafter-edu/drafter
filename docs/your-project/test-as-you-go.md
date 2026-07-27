---
page_type: how-to
title: Test as you go
level: L2
audience: S
priority: P1
prereqs: [your-project/build-one-path]
symbols: []
outcome: Keep a working app working.
---

# Test as you go

## Goal

You want the app you had yesterday to still work tomorrow, without
re-clicking everything after every change.

## Before you start

You have a [walking skeleton](build-one-path.md) with its first
test. This page is about building one habit: **every feature gets
one test, written the same day.** You do not need a full test
suite or coverage targets, only one honest assertion per feature.

## The one-test-per-feature habit

When a feature is logic, pin the rule with `assert_state`, calling
the route the way the app would:

```python
assert_state(save_entry(State([], 100.0), "2026-07-27", 8.5, "hot"),
             State([Entry("2026-07-27", 8.5, "hot")], 100.0))
```

When a feature is display, pin the important part with
`assert_has`:

```python
assert_has(index(State([], 100.0)), Button("Add a hike", "add_entry"))
```

When a feature has a failure path, test the failure too. The
[to-do list](../examples/todo-list.md) tests removing task 99 for
exactly this reason. Two tests for a feature with branches is
normal.

Rules that live in helper functions
(`hike_total(entries)`, `pet_mood(state)`) get the shortest tests
of all: `assert_equal(hike_total([...]), 8.5)`. If a rule is hard
to test, that is usually a sign it should move into a helper
function.

## Run them constantly

Tests run every time your program starts, and their results appear
in the debug panel's Tests tab. Running the tests therefore costs
nothing extra, because it already happens on every save. The
workflow that makes them pay off:

1. Change one thing.
2. Glance at the Tests tab.
3. If it is green, continue. If it is red, you just learned
   something *while the change was still fresh in your head*,
   which is the cheapest possible time to learn it.

A red test after a change you were confident about is the whole
point of the habit. Read the difference report; it shows exactly
what changed.

## Freeze the finished parts

Once a page is truly finished (say, the results screen you are
proud of), [freeze it](../add/freeze-pages.md): the debug panel's
History tab gives you the whole page as an `assert_equal` you can
paste into your program. Frozen tests guard against accidents in
places you have stopped looking at. Save them for stable pages,
because freezing a page you redesign weekly only creates noise.

## When a test fails on purpose

Deliberate changes will sometimes break honest tests. Treat a
failing test as a question ("did you mean to change this?"), and
answer it by updating the test *in the same sitting* as the
change. A test suite with failures you know about but have not
fixed trains you to ignore red results, which undoes the whole
habit.

## Common problems

- **"I'll add tests at the end"**: end-of-project tests document
  bugs instead of preventing them, and the end is when you have
  the least time. Write one test per feature on the same day; each
  one takes about two minutes.
- **A test that repeats the code's mistake**: if you produce the
  expected value by running the code and copying its answer, the
  test proves nothing. Work the expected value out by hand, or use
  a case whose answer you already know.
- **Everything breaks when State changes**: adding a field changes
  every `State(...)` call in your tests. That is annoying, but it
  is still cheaper than not having the tests. Update them and move
  on. (This is also a reason to design your
  [state](plan-your-data.md) before writing many tests.)
- **Tests pass, app is broken**: the broken part must be one with
  no test. Turn the bug you just found by hand into your next
  test, written *before* the fix, so you can tell when the fix
  works.

## You are ready for the next step when

Every existing feature has its assertion, the Tests tab is green,
and adding a feature without its test has started to feel like
leaving the house without keys. Keep building with
[Add features one at a time](add-features.md), then
[improve the design](improve-the-design.md) when the features are
in.
