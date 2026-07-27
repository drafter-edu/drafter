---
page_type: component
title: Paragraph
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - Paragraph
outcome: Use real paragraphs instead of strings.
---

# Paragraph

Group: [Text](../index.md#text)

## Description

A `Paragraph` is a real paragraph: a block of text with breathing
room above and below it, the way themes expect prose to arrive.
Plain strings with `"\n"` work fine for short labels and lines,
but multi-sentence prose reads better as paragraphs, and themes
style them deliberately. `P` is a shorter name for the same
component.

## Syntax

```python
Paragraph(text)
Paragraph(text, more_content, ...)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `*content` | strings or components | required | The paragraph's content, usually one string, optionally mixed with inline components. |

## Examples

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("About Domino"),
        Paragraph(
            "Domino arrived on a Tuesday, inspected every room "
            "twice, and accepted the household by Thursday."
        ),
        Paragraph(
            "He has opinions about closed doors and none at all "
            "about the vacuum, which unsettles the other pets."
        )
    ])


start_server(State())
```

## Notes

- Each `Paragraph` is its own block with theme-controlled spacing
  before and after; two paragraphs never need `"\n"` between
  them.
- Content can mix strings with inline components:
  `Paragraph("Press ", KeyboardInput("Enter"), " to begin.")`.
- For a line break *inside* a paragraph, use `"\n"` in the string
  as usual.

## Related components

- [Text](text.md): one styled run of text, inline.
- [BlockQuote](blockquote.md): a quoted block instead of an
  ordinary one.

## External links

- [The p element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/p)
