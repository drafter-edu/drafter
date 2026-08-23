---
page_type: component
title: InlineCode
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - InlineCode
outcome: Mark code in text.
---

# InlineCode

Group: [Text](../index.md#text)

## Description

`InlineCode` marks a short piece of code inside a sentence,
rendering it in a monospaced font the way this documentation
writes `state.score`. Use it when prose mentions a function name,
a value, or a snippet; when the code is a block with its own
lines and spacing, use [PreformattedText](pre.md) instead.

## Syntax

```python
InlineCode(text)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `*content` | strings, numbers, booleans, or components | required | The code to display, usually one short string. |

## Examples

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Python Tip of the Day"),
        Paragraph(
            "Calling ",
            InlineCode("state.treats + 1"),
            " computes a bigger number, but only ",
            InlineCode("state.treats = state.treats + 1"),
            " remembers it."
        )
    ])


start_server(State())
```

## Notes

- The content is displayed as text, angle brackets and all, so
  showing code that contains HTML is safe.
- `InlineCode` flows inside a line. It pairs naturally with
  [Paragraph](paragraph.md), as above.
- Useful beyond code pages: an app that asks visitors to type an
  exact value can show that value in `InlineCode` so it stands
  apart from the surrounding sentence.

## Related components

- [PreformattedText](pre.md): whole blocks of code or aligned
  text.
- [Inline text semantics](inline-styles.md): `KeyboardInput` and
  `SampleOutput`, the keyboard-input and program-output cousins.

## External links

- [The code element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/code)
