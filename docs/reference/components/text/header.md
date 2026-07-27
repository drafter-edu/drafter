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

A `Header` renders a heading, such as a page title or a section
title. The heading level, from 1 through 6, controls both the size of
the text and the document structure that screen readers and search
engines use to navigate the page.

## Syntax

```python
Header(body)
Header(body, level)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `body` | content | required | The heading text (or other content). |
| `level` | `int` | `1` | The heading level. Level 1 is the largest and level 6 is the smallest. A level outside 1-6 raises a friendly error. |

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

- A `Header` already appears on its own line, so you do not need to
  add `"\n"` around it.
- Use heading levels in order, without skipping any. A page should
  have one level-1 header for its title, level-2 headers for its
  sections, and level-3 headers inside those sections. Assistive
  technology navigates by this hierarchy, not by the visual size of
  the text.
- A level outside 1-6 raises
  [Header level must be between 1 and 6](../../../help/errors/header-level-invalid.md).
- To make text larger without marking it as a section title, use
  [large_font or change_text_size](../../styling-functions.md)
  instead of a Header.

## Related components

- [Text](text.md) and [Paragraph](paragraph.md) display body text.
- [HorizontalRule](../layout/horizontalrule.md) is another way to
  mark a boundary between parts of a page.

## External links

- [Heading elements on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/Heading_Elements)
