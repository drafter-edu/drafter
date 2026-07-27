---
page_type: error
title: Header level must be 1-6
level: L2
audience: S
priority: P2
prereqs: []
symbols: []
outcome: Fix an invalid Header level.
error_text: "Header level must be between 1 and 6"
---

# Header level must be 1-6

## The error

```text
Header level must be between 1 and 6, not 7
```

The friendly version: "Headers only come in six sizes, so the
level argument must be a number from 1 (biggest) to 6
(smallest)."

## What it means

`Header("Title", level)` takes a size level, and the web only has
six heading sizes. Level 1 is the biggest and 6 is the smallest;
anything outside that range (or not a whole number) stops the
page when the component is built.

## Where to look

The `Header(...)` call whose level the message quotes. If your
route builds headers in a loop or computes the level, the
computation is the real suspect.

## Check

- **A level of 0 or 7+**: often from arithmetic, like
  `level + 1` applied one time too many in nested sections.
- **The arguments swapped**: `Header(2, "Title")` puts the text
  where the level belongs. The text comes first.
- **Expecting bigger numbers to mean bigger text**: the scale
  runs the other way; 1 is the largest.

## Fix

Use a number from 1 to 6, with 1 reserved for the page's one main
title:

```python
Header("Chapter One")          # level 1, the default
Header("A section", 2)
Header("A small note", 4)
```

If a computed level can drift out of range, clamp it before the
call: `if level > 6: level = 6`.

## Confirm

The page renders and the heading appears at the size you chose.

## Prevent

Pick heading levels for document structure (one level 1, level 2
for sections, level 3 inside them) rather than for looks; needing
level 7 usually means the styling, not the structure, wanted
changing. Size adjustments belong to
[styling helpers](../../add/change-appearance/helpers.md).

## Understand

[Header](../../reference/components/text/header.md) documents the
component, and heading structure matters for screen readers, as
[Design basics](../../add/change-appearance/design-basics.md)
explains.
