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
your own app, and a button in the debug panel writes the tests.

## The workflow

1. **Run your app and click through it.** Visit each page you want
   to freeze, in the exact situation you care about (the right
   state, the right values). Drafter records every visit.
2. **Open the debug panel's Tests tab** and press **Copy Regression
   Tests**. Drafter writes one test for each page you visited and
   puts them all on your clipboard. The **Download Tests (.py)**
   button next to it saves the same tests as a file instead.
3. **Paste the tests** into your program, above
   `start_server(...)`.
4. **Delete the tests you do not want.** You get a test for every
   visit, so a page you passed through three times appears three
   times. Keep the visits that show a finished page and remove the
   rest.
5. **Save.** The Tests tab now lists the frozen tests as passing.

The pasted text begins with two comment lines and its own
`from drafter import *` line. All three are harmless, and you can
delete them if your file already has the import.

Each test has the same shape. This one is from the chore list in
[Show a collection](show-a-collection.md), after pressing "Done" on
the second chore:

```python
assert_equal(finish_chore(State(chores=['Feed the cats', 'Walk the dogs', 'Water the plants']), 1),
    Page(State(chores=['Feed the cats', 'Water the plants']), [
        Header("Today's chores"),
        'Feed the cats ',
        Button('Rename', 'edit_chore', arguments=Argument('position', 0)),
        Button('Done', 'finish_chore', arguments=Argument('position', 0)),
        '\n',
        'Water the plants ',
        Button('Rename', 'edit_chore', arguments=Argument('position', 1)),
        Button('Done', 'finish_chore', arguments=Argument('position', 1)),
        '\n',
    ]))
```

The first argument is the route call that built the page, with the
state and the parameters as they were at that moment. The second
argument is the complete page the route returned. `assert_equal`
compares any two values and reports every difference it finds, so a
failing frozen test shows exactly which piece of the page changed.

## Freeze one page

To freeze a single visit, use the History tab instead of the Tests
tab. Find the visit in the list and expand **Page shown** underneath
it. Drafter displays that one visit as a complete `assert_equal`
test, which you can select, copy, and paste above
`start_server(...)`.

A generated test spells out every value in full. You may shorten it
by hand when your program already has a name for a long value, as
[Finish and test an app](../tutorials/finishing.md) does with its
list of compliments.

## When to freeze, and when not to

Freeze pages that are **finished and stable**: the results screen,
the landing page, a formatted report. The freeze protects work you
do not intend to touch again.

For pages that are still changing, and for large, busy pages, prefer
hand-written assertions. A frozen test on such a page fails on every
small tweak, which trains you to ignore failures. A couple of
`assert_has` checks on the parts that matter
(`assert_has(results(state), "You scored 3 out of 3.")`) hold up far
better.

## Updating a stale frozen test

When you *deliberately* redesign a frozen page, its test fails, and
it should: the test is asking whether you meant to change the page.
Answer by re-freezing: visit the redesigned page, copy its new test
from the History tab, and replace the old test with it. Delete
frozen tests for pages that no longer exist.

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
- **You changed a color or a theme and expected a frozen test to
  fail**: it will not. `assert_equal` ignores styling unless you ask
  for `strict_styles=True`, so colors, fonts, sizes, and themes can
  change freely. A frozen test fails when the words, the order, or
  the kind of component on the page changes, for example when plain
  text becomes a `Header`.
- **A frozen test passes on some runs and fails on others**: the page
  came from a route that uses `random`. Do not freeze that page. Test
  the part that does not depend on chance, as in
  [a random result you can still test](show-different-content.md#recipe-a-random-result-you-can-still-test).

## Understand it

Frozen tests are a kind of regression test, which is a test that
checks finished work has not changed.
[Finish and test an app](../tutorials/finishing.md) walks through
the whole cycle of freezing a page, breaking it, and fixing it.

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
