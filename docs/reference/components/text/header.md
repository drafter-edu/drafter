---
page_type: component
title: Header
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - Header
outcome: Add section headings, levels 1-6.
---

# Header

Group: [Text](../index.md#text)

## Description

A `Header` renders a heading: big for page titles, smaller for section
titles. The level, 1 through 6, controls both the size and the
document structure that screen readers and search use to navigate.

## Syntax

```python
Header(body)
Header(body, level)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `body` | content | required | The heading text (or other content). |
| `level` | `int` | `1` | The heading level: 1 is the biggest, 6 the smallest. Anything outside 1-6 raises a friendly error. |

Like every component, `Header` also accepts
[styling and attribute keywords](../../keyword-attributes.md).

## Examples

```python drafter height=280
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Pet of the Month"),
        Header("Winner: Domino", 2),
        "A black cat of considerable dignity.\n",
        Header("Runner-up: Babbage", 2),
        "A small black mutt of considerable enthusiasm.\n"
    ])


start_server()
```

## Notes

- Headers already sit on their own line; no `"\n"` needed around them.
- Use levels in order without skipping: one level-1 header for the
  page, level 2 for its sections, level 3 inside those. That
  hierarchy, not the visual size, is what assistive tech navigates by.
- A level outside 1-6 raises
  [Header level must be between 1 and 6](../../../help/errors/header-level-invalid.md).
- To make text merely bigger without meaning "section title", use
  [large_font or change_text_size](../../styling-functions.md)
  instead of a Header.

## Related components

- [Text](text.md) and [Paragraph](paragraph.md): body text.
- [HorizontalRule](../layout/horizontalrule.md): another way to mark
  a boundary.

## External links

- [Heading elements on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/Heading_Elements)
