---
page_type: component
title: BlockQuote
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - BlockQuote
outcome: Quote a passage.
---

# BlockQuote

Group: [Text](../index.md#text)

## Description

A `BlockQuote` sets a quoted passage apart from your own prose,
usually indented, sometimes with a decorative bar, depending on
the theme. Use it for reviews, testimonials, quoted messages, or
any text your app repeats from another voice.

## Syntax

```python
BlockQuote(cite, text)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `cite` | `str` or `None` | required | The URL the quote comes from, recorded invisibly for the curious. Pass `None` when there is no source URL. |
| `*content` | strings, numbers, booleans, or components | required | The quoted text. |

## Examples

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("What Our Customers Say"),
        BlockQuote(None,
                   "Five stars. The corgi at the counter "
                   "approved my order personally."),
        "- A satisfied visitor"
    ])


start_server(State())
```

## Notes

- The `cite` URL comes first and is required, which surprises
  people; `None` is the normal value for quotes without a web
  source.
- The attribution line ("- A satisfied visitor") goes outside the
  quote, as ordinary content, because it is your voice rather
  than the quoted one.
- For a short quotation inside a sentence, use the
  `InlineQuotation` component from the
  [inline text family](inline-styles.md) instead.

## Related components

- [Paragraph](paragraph.md): ordinary prose blocks.
- [Inline text semantics](inline-styles.md): `InlineQuotation`
  for quotes within a line.

## External links

- [The blockquote element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/blockquote)
