---
page_type: component
title: PreformattedText
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Pre
  - PreformattedText
outcome: Preserve spacing and newlines.
---

# PreformattedText

Group: [Text](../index.md#text)

## Description

`PreformattedText` displays text exactly as you wrote it: every
space, every newline, in a monospaced font where all characters are
the same width. Normal page text collapses runs of spaces and
ignores where your string breaks its lines; preformatted text keeps
them. Use it for anything where the layout of the characters is the
point: ASCII art, aligned columns, or program output. `Pre` is a
shorter name for the same component.

## Syntax

```python
PreformattedText(text)
PreformattedText(text, more_text, ...)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `*content` | `str` or components | required | The content to display with spacing preserved. Usually one multi-line string. |

## Examples

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    scoreboard = (
        "PET       TREATS   NAPS\n"
        "Ada           12      3\n"
        "Captain        2     14\n"
        "Domino         5      9"
    )
    return Page(state, [
        Header("Daily Report"),
        PreformattedText(scoreboard)
    ])


start_server(State())
```

## Notes

- Ordinary strings in a page need `"\n"` to break lines, and
  multiple spaces in them collapse into one. Inside
  `PreformattedText`, both are kept as written, which is what makes
  the columns above line up.
- The monospaced font is what makes alignment work: count
  characters, not pixels.
- Long lines do not wrap; they can make the page scroll sideways.
  Break lines yourself where you want them.
- For a short piece of code inside a sentence, use
  [InlineCode](inlinecode.md) instead of a whole preformatted
  block.

## Related components

- [InlineCode](inlinecode.md): code-styled text within a line.
- [Text](text.md): a single run of normal text with styling.

## External links

- [The pre element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/pre)
