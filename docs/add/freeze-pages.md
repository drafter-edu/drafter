---
page_type: how-to
title: Freeze finished pages
level: L3
audience: S
priority: P1
prereqs: [add/test-a-feature]
symbols: []
outcome: Auto-generate regression tests from page history.
---

# Freeze finished pages

## Goal

A page of your app is finished and you want it to stay that way: any
future change that accidentally alters it should fail a test, not
surprise a visitor.

## Before you start

You can write an `assert_state` or `assert_has` test by hand
([Test a feature](test-a-feature.md)). Freezing is different in
spirit: instead of asserting a rule you chose, you record a whole
page you approved. Drafter does the recording for you while you use
your own app.

## The workflow

1. **Run your app and visit the page** you want to freeze, in the
   exact situation you care about (the right state, the right
   values).
2. **Open the debug panel's History tab.** Every visit is listed
   with the route call that produced it.
3. **Expand the visit's Response.** It shows the complete
   `Page(...)` your route returned, written out as Python you can
   copy.
4. **Assemble the test** above `start_server(...)`: the call on the
   left, the page on the right.

The result looks like this (from the compliment machine in
[Finish and test an app](../tutorials/finishing.md)):

```python
assert_equal(index(State(COMPLIMENTS, 0)),
             Page(State(COMPLIMENTS, 0), [
                 Header("The Compliment Machine"),
                 "Your code is looking sharp today.\n",
                 Button("Another, please", "another")
             ]))
```

`assert_equal` compares any two values and reports every difference
it finds; for frozen pages, that means a failure shows exactly which
piece of the page changed.

The Tests tab can also **copy or download every test** the app has
run as a ready-to-save Python file, which is a quick way to collect
your frozen tests once you have a few.

## When to freeze, and when not to

Freeze pages that are **finished and stable**: the results screen,
the landing page, a formatted report. The freeze protects work you
do not intend to touch again.

Prefer hand-written assertions for pages still changing, and for big
busy pages, where a frozen test fails on every tweak and trains you
to ignore failures. A couple of `assert_has` checks on the parts
that matter
(`assert_has(results(state), "You scored 3 out of 3.")`) age far
better there.

## Updating a stale frozen test

When you *deliberately* redesign a frozen page, its test fails, and
should: that is the "did you mean to change this?" question being
asked. Answer it by re-freezing: visit the redesigned page, copy the
new `Page(...)` from the History tab, and replace the old expected
value. Delete frozen tests for pages that no longer exist.

## Common problems

- **The frozen test fails the moment you paste it**: the state in
  your copied call does not reproduce the page you froze, often
  because the page depended on earlier clicks. Reproduce the
  situation, then freeze from that visit.
- **"Circular Reference" appears inside the recorded page**: your
  state contains objects that refer to each other, which the
  recorder cannot flatten. See
  [Circular Reference in generated tests](../help/errors/circular-reference-tests.md).
- **The frozen page is huge and the test is unreadable**: freeze
  smaller pages, or switch that page to a few `assert_has` checks.
- **Every tiny styling tweak breaks a frozen test**: that is the
  deal you signed. Freeze after the styling pass, not before; the
  [finishing tutorial](../tutorials/finishing.md) orders the steps
  that way on purpose.

## Understand it

Frozen tests are regression tests: the concept is introduced at the
end of [Test a feature](test-a-feature.md), and
[Finish and test an app](../tutorials/finishing.md) walks the whole
freeze-break-fix loop.

## See another example

[Finish and test an app](../tutorials/finishing.md) freezes the
compliment machine and then breaks it on purpose.

## Look it up

[Testing functions](../reference/testing-functions.md) for
`assert_equal` and its options;
[See inside your app](../start/debug-panel.md) for the debug panel
tour.

## Fix a problem

[Circular Reference appears in generated tests](../help/errors/circular-reference-tests.md).
