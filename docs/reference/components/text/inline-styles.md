---
page_type: component
title: Inline text semantics
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - Strong
  - Emphasis
  - MarkedText
  - KeyboardInput
  - SampleOutput
  - SmallText
  - Superscript
  - Subscript
  - InlineVariable
  - InlineQuotation
  - DefinitionTerm
  - Abbreviation
  - DeletedText
  - InsertedText
outcome: Use the inline semantic text components.
---

# Inline text semantics

Group: [Text](../index.md#text)

## Description

Fourteen small components mark what a piece of text *means*
(important, emphasized, deleted, a keyboard key), and browsers
and themes style the meaning (bold, italics, strikethrough, a
key-shaped box). They share one page because they share one
shape: wrap the text, use inside a line. Reach for these when the
meaning is real; when you only want a look, with no meaning
behind it, use styling keywords on [Text](text.md) instead.

## Syntax

```python
Strong(text)
Emphasis(text, more_content, ...)
Abbreviation("HTML", title="HyperText Markup Language")
```

All of them accept any number of content items. Three carry an
extra keyword: `InlineQuotation` and the edit pair take `cite`
(a source URL), `DefinitionTerm` and `Abbreviation` take `title`
(the tooltip text), and the edit pair also takes `datetime`
(when the change happened).

## Parameters

| Component | Typical look | Marks |
| --------- | ------------ | ----- |
| `Strong` | **bold** | Seriously important text. |
| `Emphasis` | *italics* | A word you would stress out loud. |
| `MarkedText` | highlighted | Text relevant right now, like a search hit. |
| `KeyboardInput` | key style | Something the visitor should type or press. |
| `SampleOutput` | monospace | Something a program printed. |
| `SmallText` | smaller | Fine print and side comments. |
| `Superscript` | raised | Exponents, ordinals. |
| `Subscript` | lowered | Chemical formulas, indices. |
| `InlineVariable` | italics | A variable name in prose. |
| `InlineQuotation` | "quoted" | A short quote inside a sentence. |
| `DefinitionTerm` | italics | The term a sentence is defining. |
| `Abbreviation` | dotted underline | An abbreviation; `title` holds the expansion. |
| `DeletedText` | ~~strikethrough~~ | Text edited away. |
| `InsertedText` | underline | Text edited in. |

## Examples

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("House Rules"),
        Paragraph(
            Strong("Never"), " leave the treat jar open. ",
            Emphasis("Captain is always watching.")
        ),
        Paragraph(
            "Press ", KeyboardInput("Ctrl"), " + ",
            KeyboardInput("S"), " to save your progress."
        ),
        Paragraph(
            "Dinner is at ", DeletedText("5:00"), " ",
            InsertedText("4:45"),
            SmallText(" (the cats renegotiated).")
        ),
        Paragraph(
            "The ", Abbreviation("ASPCA",
                title="American Society for the Prevention of "
                      "Cruelty to Animals"),
            " approves of this household."
        )
    ])


start_server(State())
```

## Notes

- Meaning is the point: screen readers can convey `Strong` and
  `DeletedText`, while a bold look applied with styling keywords
  is only a look. When the text genuinely carries the meaning,
  the semantic component is the better choice.
- These are inline components; they sit inside sentences and
  pair naturally with [Paragraph](paragraph.md).
- The `title` keyword of `Abbreviation` and `DefinitionTerm`
  appears when hovering, which touch screens cannot do; include
  the expansion in visible text at least once.
- `DeletedText` and `InsertedText` accept `cite` and `datetime`
  keywords recording where and when the change was decided,
  invisible but machine-readable.

## Related components

- [Text](text.md): looks without meaning, via styling keywords.
- [InlineCode](inlinecode.md): the code-in-a-sentence sibling.
- [BlockQuote](blockquote.md): quotations too big for
  `InlineQuotation`.

## External links

- [Inline text semantics on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements#inline_text_semantics)
