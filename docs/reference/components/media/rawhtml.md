---
page_type: component
title: RawHTML and HtmlTag
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - RawHTML
  - HtmlTag
outcome: Use the escape hatch to raw HTML safely.
---

# RawHTML and HtmlTag

Group: [Media](../index.md#media)

## Description

Two escape hatches for HTML that no component covers. `HtmlTag`
renders one tag of your choosing around normal Drafter content,
keeping all of Drafter's safety. `RawHTML` renders a string as
HTML exactly as written, keeping none of it. Prefer the
component catalog first, `HtmlTag` second, and `RawHTML` last;
the [Embed HTML guide](../../../add/html.md) walks the
decision.

## Syntax

```python
HtmlTag(tag, content, ...)
RawHTML(html)
```

## Parameters

For `HtmlTag`:

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `tag` | `str` | required | The HTML tag name, like `"u"` or `"cite"`. |
| `*content` | strings or components | required | Normal Drafter content, escaped and safe as always. |

For `RawHTML`:

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `html` | `str` | required | Markup rendered exactly as written, with no escaping. |

## Examples

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Two escape hatches"),
        Paragraph(
            "HtmlTag wraps safe content: ",
            HtmlTag("cite", "The Care and Feeding of Corgis"),
            "."
        ),
        RawHTML("<p>RawHTML renders <em>anything</em>, "
                "as written.</p>")
    ])


start_server(State())
```

## Notes

- **The safety rule for `RawHTML`**: never put text a visitor
  typed inside it. Form values, state that forms filled, and
  uploaded file contents can all contain HTML, and `RawHTML`
  would execute it, script tags included. Content you wrote
  yourself is fine.
- `HtmlTag` has no such risk: its content goes through the same
  escaping as everything else, so only the tag itself is yours
  to get right.
- `RawHTML` renders inside a `div`, so it behaves as a block on
  the page.
- Tests match a `RawHTML` by its exact string
  (`assert_has(page, RawHTML("<p>...</p>"))`) and cannot see
  text inside the blob, one more reason components test better.
- `HtmlTag` accepts styling keywords and `classes` like any
  component; the inside of a `RawHTML` can only be styled with
  [custom CSS](../../../add/change-appearance/custom-css.md).

## Related components

- [Text](../text/text.md) and the
  [inline semantics family](../text/inline-styles.md): the
  components that usually make `HtmlTag` unnecessary.

## External links

- [Embed HTML](../../../add/html.md): the how-to with the full
  safety discussion.
- [Security honestly](../../../extend/security.md): why escaping
  exists.
