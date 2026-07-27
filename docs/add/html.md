---
page_type: how-to
title: Embed HTML
level: L3
audience: S
priority: P2
prereqs: [add/change-appearance/custom-css]
symbols: []
outcome: Use raw HTML when components are not enough.
---

# Embed HTML

## Goal

You know some HTML and want to use a piece of it that no Drafter
component provides: an unusual tag, a snippet copied from a
tutorial, or an embed code a service handed you.

## Before you start

This is the last resort, on purpose. When a component exists for
what you want, the component version is shorter, safer, and works
with tests and styling helpers; skim the
[component list](../reference/components/index.md) before
reaching for raw HTML. You should also know basic HTML from the
[custom CSS](change-appearance/custom-css.md) work.

One rule before anything else: text on a Drafter page is text.
If you write `"<b>hello</b>"` in your page content, visitors see
those angle brackets, because Drafter escapes strings rather than
interpreting them. That protection is deliberate, and the
components below are the doors through it.

## Recipe: one unusual tag

`HtmlTag` renders any tag you name, wrapped around normal Drafter
content. The content stays escaped and safe; only the tag is
yours:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adoption Contract"),
        "I promise to give ",
        HtmlTag("u", "Babbage"),
        " belly rubs ",
        HtmlTag("u", "every single day"),
        "."
    ])


start_server(State())
```

## Recipe: a block of real HTML

`RawHTML` renders a string as HTML, exactly as written, with no
escaping at all:

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("From the old website"),
        RawHTML(
            "<blockquote cite='https://example.com'>"
            "<p>Domino remains the <em>only</em> cat to have"
            " been elected mayor of the living room.</p>"
            "</blockquote>"
        )
    ])


start_server(State())
```

## The safety rule

`RawHTML` turns off the text-stays-text protection, so it comes
with one absolute rule: **never put text a visitor typed inside
`RawHTML`**. A visitor who types HTML into a form field would
have that HTML executed, script tags included. Content you wrote
yourself is fine; content from a form parameter, state that a
form filled, or an uploaded file is not. Displayed as ordinary
strings, those same values are harmless.

## Common problems

- **The HTML shows up as literal text with angle brackets**: it
  was passed as a plain string. Wrap it in `RawHTML` if it is
  really meant to be markup.
- **The snippet needs script tags or external files**: script
  tags inside `RawHTML` will run, but embeds that load outside
  resources may be blocked or behave differently once deployed;
  test the deployed site early.
- **Tests cannot find the content**: assertions see `RawHTML` as
  one blob. `assert_has(page, RawHTML(...))` with the identical
  string works; matching text inside it does not. One more
  reason to prefer components.
- **Styling helpers do not reach inside**: `HtmlTag` accepts
  `style_` keywords and `classes` like any component, but the
  interior of a `RawHTML` blob is beyond the helpers; style it
  with [custom CSS](change-appearance/custom-css.md) instead.

## Understand it

[Security honestly](../extend/security.md) explains the escaping
protection this page pokes holes in, and why the safety rule is
absolute.

## See another example

The [RawHTML and HtmlTag reference page](../reference/components/media/rawhtml.md)
shows both components with their parameters.

## Look it up

[RawHTML and HtmlTag](../reference/components/media/rawhtml.md),
and the [component list](../reference/components/index.md) for
the component you might be about to rebuild by hand.

## Fix a problem

[Page content invalid](../help/errors/page-content-invalid.md)
covers what happens when a page is handed something that is not
valid content.
