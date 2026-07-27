---
page_type: component
title: Text
level: L2
audience: S
priority: P1
prereqs: []
symbols:
  - Text
outcome: Use the explicit text component.
---

# Text

Group: [Text](../index.md#text)

## Description

`Text` displays a piece of text, exactly like putting a plain
string in your page. The difference is that a `Text` component can
carry styling keywords and attributes, while a bare string cannot.
Reach for it when one run of text needs its own color, size, or
class; everywhere else, plain strings are the normal way to put
text on a page.

## Syntax

```python
Text(body)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `body` | `str` | required | The text to display. |

## Examples

The first line is a plain string; the second is a `Text` with
styling keywords attached:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        "Domino is a perfectly ordinary black cat.\n",
        Text("Except at 3 AM.", style_color="crimson",
             style_font_weight="bold")
    ])


start_server(State())
```

## Notes

- A `Text` with no extra settings renders as bare text, and even
  compares equal to the matching plain string, so
  `assert_has(page, "Except at 3 AM.")` finds it either way.
- When it does carry settings, `Text` renders as an inline span:
  it flows within the line rather than starting a new block. Add
  `"\n"` after it when the next thing should start on a new line.
- For whole paragraphs with their own spacing, use
  [Paragraph](paragraph.md); for meaning rather than looks (strong
  emphasis, quoted text), see the
  [inline text components](inline-styles.md).

## Related components

- [Span](../layout/span.md): the same inline grouping for a mix of
  text and components.
- [Paragraph](paragraph.md): block-level paragraphs.

## External links

- [The span element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/span)
