---
page_type: component
title: Span
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - Span
outcome: Group content inline.
---

# Span

Group: [Layout](../index.md#layout)

## Description

A `Span` groups content *inline*: it flows along with surrounding
text instead of starting a new line the way a [Div](div.md) does.
Use it to style or tag a few words inside a sentence, or to give a
[Fragment](../../fragment.md) a small inline target.

## Syntax

```python
Span(content, more_content, ...)
```

## Parameters

`Span` takes any number of strings and components as positional
arguments. Like every component, it accepts
[styling and attribute keywords](../../keyword-attributes.md).

## Examples

```python drafter height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        "The potion is ",
        Span("extremely",
             style_color="crimson",
             style_text_transform="uppercase"),
        " unstable, but the label is ",
        Span("reassuring", id="mood"),
        ".\n",
        Button("Shake it", "shake")
    ])


@route
def shake() -> Fragment:
    return Fragment(["no longer reassuring"], target="#mood")


start_server()
```

## Notes

- Everything here stays on one line: spans join the sentence, and
  the fragment swaps three words without disturbing it.
- The [styling helpers](../../styling-functions.md) wrap strings in
  inline text automatically, so `bold("word")` already does the
  common case; reach for `Span` when grouping several things or
  attaching an `id`/`classes`.

## Related components

- [Div (Box)](div.md): the block-level sibling.
- [Inline text semantics](../text/inline-styles.md): Strong,
  Emphasis, and friends, when the grouping has meaning.

## External links

- [The span element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/span)
