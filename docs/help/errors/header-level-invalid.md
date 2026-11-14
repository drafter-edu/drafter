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

The error page has this title:

```text
Unusable Value
```

Drafter uses the title "Unusable Value" for several different
problems, so the sentence under the title is what identifies this
one:

```text
Headers only come in six sizes, so the level argument must be a number
from 1 (biggest) to 6 (smallest).
```

The technical message below it shows the level your code gave:

```text
request.route_execution_failed: Error while processing request for URL 'index':
Header level must be between 1 and 6, not 7
```

## What it means

`Header("Title", level)` takes a size level, and the web only has
six heading sizes. Level 1 is the biggest and 6 is the smallest. A
level below 1 or above 6 stops the page when the component is
built.

## Where to look

The `Header(...)` call whose level the message quotes. If your
route builds headers in a loop or computes the level, the
computation is the real suspect.

## Check

- **A level of 0 or 7+**: often from arithmetic, like
  `level + 1` applied one time too many in nested sections.
- **The arguments swapped**: `Header(2, "Title")` puts the text
  where the level belongs. This mistake produces a different error
  page, titled "Type Mismatch", whose technical message ends
  `'<' not supported between instances of 'str' and 'int'`. The text
  comes first and the level second.
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
