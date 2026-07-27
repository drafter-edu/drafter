---
page_type: error
title: SelectBox default not in options
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Fix a SelectBox default that is not among its options.
error_text: "is not in options"
---

# SelectBox default not in options

## The error

```text
default_value 'Chocolate' is not in options ['vanilla', 'chocolate', 'strawberry']
```

The friendly version: "The starting choice for this SelectBox has
to be one of the options in its list."

## What it means

A `SelectBox` shows a dropdown of options with one pre-chosen; the
pre-chosen one must literally be in the list, and yours is not. The
error happens when the component is built, so the page stops before
rendering.

## Where to look

The `SelectBox(...)` call whose default and options the message
quotes.

## Check

The message shows both sides; compare them character by character:

- **Capitalization**: `'Chocolate'` is not `'chocolate'`; matching
  is exact.
- **A stale state value**: `SelectBox("flavor", options,
  state.flavor)` breaks when the state holds something no longer in
  the list, often after you edited the options.
- **A default that was never an option**: fine, if you meant it;
  add it to the list or drop the default entirely (no third
  argument pre-selects the first option).

## Fix

Make them agree:

```python
SelectBox("flavor", ["vanilla", "chocolate", "strawberry"], "chocolate")
```

For the rare case where a not-in-list default is intentional,
`allow_missing=True` switches the check off.

## Confirm

The page renders with the intended option pre-chosen.

## Prevent

When the default comes from state, initialize that state field to
one of the options, and update it in the same commit whenever the
options list changes.

## Understand

[SelectBox](../../reference/components/input/selectbox.md) has the
full parameter story.
