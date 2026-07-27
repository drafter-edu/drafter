---
page_type: component
title: LineBreak
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - LineBreak
outcome: Force a new line.
---

# LineBreak

Group: [Layout](../index.md#layout)

## Description

A `LineBreak` starts a new line. Drafter renders page content in a
row, side by side, until something breaks the line, and `LineBreak()`
is the explicit way to do that. Ending a string with `"\n"` does the
same job and is what most examples in these docs use; `LineBreak()`
is useful when there is no convenient string to attach the `"\n"` to.

## Syntax

```python
LineBreak()
```

## Parameters

`LineBreak` takes no positional parameters. Like every component, it
accepts [styling and attribute keywords](../../keyword-attributes.md).

## Examples

```python drafter height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        "These two fields sit on separate lines because of the break:",
        LineBreak(),
        TextBox("first_word"),
        LineBreak(),
        TextBox("second_word"),
        LineBreak(),
        Button("Combine", "index")
    ])


start_server()
```

## Notes

- One `LineBreak` starts a new line; several in a row add empty
  space, though [change_margin](../../styling-functions.md) is the
  better tool for deliberate spacing.
- A `"\n"` inside or at the end of a string is equivalent
  (`"Score: 3\n"`), and a string containing only `"\n"` is a
  convenient way to break between two components.
- Headers, lists, and other block components already start their own
  lines; breaks around them do nothing visible.

## Related components

- [HorizontalRule](horizontalrule.md): draws a visible divider
  rather than only starting a new line.
- [Div (Box)](div.md) and [Row](row.md): provide deliberate layout
  when line breaks are not enough.

## External links

- [The br element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/br)
