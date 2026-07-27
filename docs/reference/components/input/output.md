---
page_type: component
title: Output
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - Output
outcome: Show a computed result region.
---

# Output

Group: [Input](../index.md#input)

## Description

An `Output` is a named region for showing a computed result. Its
name gives [Fragment](../../fragment.md) responses a ready-made
target, which makes it the natural display area for live
behavior: the route computes, the fragment lands in the output,
the rest of the page never moves.

## Syntax

```python
Output(name, content)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The region's name, which doubles as its id for fragment targeting. |
| `content` | strings or components | required | What the region shows before any update arrives. |
| `for_id` | `str` or a form component | none | The input this result was computed from, recorded for assistive technology. |

## Examples

The tip calculator recomputes on every keystroke, and only the
output region changes:

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Tip Calculator"),
        "Bill amount:",
        TextBox("bill", "20", on_input="recalculate"),
        "\n",
        Output("tip", ["A 20% tip would be $4.00"])
    ])


@route
def recalculate(bill: str) -> Fragment:
    if not bill.isdigit():
        return Fragment(["Enter a whole number of dollars."],
                        target="#tip")
    amount = int(bill) * 0.2
    return Fragment(["A 20% tip would be $" + str(round(amount, 2))],
                    target="#tip")


start_server()
```

## Notes

- Target an output by its name with a `#` prefix:
  `Fragment([...], target="#tip")`.
- The starting content matters: it shows before any event fires,
  so make it a sensible default rather than empty.
- Any component can be a fragment target if you give it an `id`;
  `Output` saves that step and tells assistive technology the
  region holds a result.
- `for_id` accepts the input component itself:
  `Output("tip", [...], for_id=the_textbox)` associates the
  result with the field it came from.

## Related components

- [Fragment](../../fragment.md): the response type that fills
  the region.
- [TextBox](textbox.md): the usual source of the events.

## External links

- [Add live behavior](../../../add/live-behavior.md): the recipes
  this component serves.
- [The output element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/output)
