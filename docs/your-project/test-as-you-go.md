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
test. The habit this page installs: **every feature ships with one
test, written the same day.** Not a test suite, not coverage
targets; one honest assertion per feature, forever.

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

When a feature has a failure path, test the failure too; the
[to-do list](../examples/todo-list.md) tests removing task 99 for
exactly this reason. Two tests for a branchy feature is normal.

Rules that live in helper functions
(`hike_total(entries)`, `pet_mood(state)`) get the simplest tests
of all: `assert_equal(hike_total([...]), 8.5)`. If a rule is hard
to test, that is usually the rule asking to become a helper.

## Run them constantly

Tests run every time your program starts and report to the debug
panel's Tests tab, so "run the tests" costs nothing; you are
already doing it on every save. The workflow that makes them pay:

1. Change one thing.
2. Glance at the Tests tab.
3. Green: continue. Red: you just learned something *while the
   change was still fresh in your head*, which is the cheapest
   possible time to learn it.

A red test after a change you believed in is the whole point of
the habit. Read the difference report; it says exactly what
changed.

## Freeze the finished parts

Once a page is done-done (the results screen you are proud of),
[freeze it](../add/freeze-pages.md): the debug panel's History tab
gives you the whole page as a pasteable `assert_equal`. Frozen
tests guard against accidents in places you have stopped looking
at. Save them for stable pages; freezing a page you redesign
weekly just manufactures noise.

## When a test fails on purpose

Deliberate changes break honest tests. The rule: a failing test is
a question ("did you mean to change this?"), and you answer it by
updating the test *in the same sitting* as the change. A test
suite with known-stale failures trains you to ignore red, which
quietly cancels the whole habit.

## Common problems

- **"I'll add tests at the end"**: end-of-project tests document
  bugs instead of preventing them, and the end is when you have
  the least time. One per feature, same day; it is two minutes.
- **A test that repeats the code's mistake**: writing the expected
  value by running the code and copying its answer proves nothing.
  Work the expected value out by hand, or from a case you know
  cold.
- **Everything breaks when State changes**: adding a field changes
  every `State(...)` call in your tests. Annoying, real, and still
  cheaper than the alternative; update them and move on. (This is
  also a nudge to design [state](plan-your-data.md) before mass
  test-writing.)
- **Tests pass, app is broken**: the broken part has no test. The
  bug you just found by hand is the next test you write, *before*
  fixing it, so you know the fix fixed it.

## You are ready for the next step when

Every existing feature has its assertion, the Tests tab is green,
and adding a feature without its test has started to feel like
leaving the house without keys. Keep building with
[Add features one at a time](add-features.md), then
[improve the design](improve-the-design.md) when the features are
in.
