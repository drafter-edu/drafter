---
page_type: error
title: Circular Reference appears in generated tests
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Handle circular references in generated tests.
error_text: "Circular Reference"
---

# Circular Reference appears in generated tests

## The error

This one does not arrive as an error page. Instead, the text
`Circular Reference` appears inside a recorded page or state in the
debug panel's History tab, right where a real value should be, and any
[frozen test](../../add/freeze-pages.md) copied from it fails or
looks wrong.

## What it means

Drafter writes out your state as Python code you can paste into
tests. That only works for values that can be written down. A
*circular reference*, where two objects each contain the other,
cannot be written down: the process would never finish. Instead of
hanging, Drafter puts the marker text where the cycle began.

## Where to look

Look at your state's structure, especially dataclasses whose fields
hold other dataclasses or lists of them. Somewhere, following the
fields leads in a loop back to where it started.

## Check

Cycles usually appear in one of these ways:

- **A list appended to itself**: `items.append(items)`.
- **A back-pointer**: a `Pet` holding its `Owner` while the `Owner`
  holds its pets.
- **Self-reference**: an object stored in one of its own fields.

Once you find the cycle, ask whether you intended it. Cycles are
legitimate for genuinely graph-shaped data, but most course apps do
not need them and only acquire one by accident.

## Fix

If the cycle is an accident, break it: store a name or an index
instead of a back-pointer (`owner_name: str` rather than
`owner: Owner`), and look the object up when needed, the way the
[shop example](../../examples/shop.md) finds items by name.

If the cycle is intentional, keep it, and write those tests by
hand instead of freezing: capture the route's result and assert on
its pieces
(`assert_equal(result.state.items[0].name, "First Item")`), which
never needs to write the whole cycle down.

## Confirm

New history entries show real values where the marker used to be
(or, for intentional cycles, your hand-written tests pass).

## Prevent

Prefer names and positions over object back-pointers in state, and
check the History tab's recorded state early in development. The
marker appears as soon as a cycle exists, long before it turns into
a confusing test.

## Understand

[Freeze finished pages](../../add/freeze-pages.md) explains what
the recorder does; [State](../../concepts/state.md) covers
designing state that stays writable.
