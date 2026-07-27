---
page_type: how-to
title: Build your own components
level: L4
audience: S
priority: P2
prereqs: [extend/javascript]
symbols: []
outcome: Create reusable components.
---

# Build your own components

## Goal

Package a piece of page you keep rebuilding into something you
can use like a built-in component. There are three levels, and
the first one covers almost everyone.

## Before you start

You can build pages comfortably and have repeated yourself at
least once; repetition is what components cure. The levels
escalate in power and difficulty together, so start at level
one and climb only when a level genuinely cannot express what
you want.

## Level 1: a function that returns components

A "component" can be nothing more than a function returning the
content you keep writing. It composes, takes parameters, and
needs no new concepts:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


def PetCard(name: str, species: str, motto: str) -> PageContent:
    return Div(
        Header(name, 3),
        Emphasis(species),
        Paragraph('"' + motto + '"'),
        style_border="2px solid #888",
        style_padding="8px",
        style_margin="8px"
    )


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Residents"),
        PetCard("Ada", "corgi", "Every walk is the best walk."),
        PetCard("Captain", "grey cat", "I was here first."),
        PetCard("Domino", "black cat", "You saw nothing.")
    ])


start_server(State())
```

Name these functions like components (`PetCard`, not
`make_pet_card`) and keep them pure: parameters in, content out,
no state mutation. This level is enough for cards, banners,
navigation bars, and any repeated furniture.

## Level 2: RawHTML for markup no component makes

When the structure you need has no component equivalent, a
function can wrap [RawHTML](../reference/components/media/rawhtml.md).
You gain arbitrary markup and lose Drafter's safety, so the
[safety rule](../add/html.md) applies in full: only your own
text, never a visitor's, goes into the markup.

```python
def Badge(label: str) -> PageContent:
    return RawHTML(
        '<span style="border-radius: 9px; background: gold; '
        'padding: 2px 8px;">' + label + "</span>"
    )
```

(Calling `Badge(user_typed_text)` would break the rule; even at
level 2, keep visitor text out.)

## Level 3: a real Component class

Real components subclass `Component` and describe their
rendering with the `RenderPlan` API, the same machinery the
built-ins use. This buys equality for tests, styling keywords,
and multi-element rendering, at the cost of touching Drafter's
internals:

```python
from drafter.components import Component, PageContent
from drafter.components.page_content import ComponentArgument, RenderPlan


@dataclass(repr=False)
class AdBox(Component):
    tag = "div"
    product: str
    text: str

    ARGUMENTS = [
        ComponentArgument("product", is_content=True),
        ComponentArgument("text", is_content=True),
    ]

    def __init__(self, product: str, text: str, **kwargs):
        self.product = product
        self.text = text
        self.extra_settings = kwargs

    def get_children(self, context):
        return [
            RenderPlan(kind="tag", tag_name="hr"),
            RenderPlan(kind="tag", tag_name="section", children=[
                RenderPlan(kind="tag", tag_name="h3",
                           children=[self.product]),
                RenderPlan(kind="tag", tag_name="p",
                           children=[self.text]),
            ]),
        ]
```

The library's own `SelectBox`, `CheckBox`, and `Table` are the
reference implementations to read next. Beyond this lies level
four, interactive custom elements with a TypeScript half (how
`Timer` and `Map` work), which is
[developer-docs](../dev/architecture.md) territory.

## Common problems

- **The level-1 function mutates state**: then it is secretly a
  route helper, not a component. Pass values in; return content
  out.
- **Tests cannot match the level-2 markup**: `assert_has` sees a
  `RawHTML` blob, matched only by its exact string. Level 1
  components test naturally; another reason to prefer them.
- **A level-3 field leaks into the rendering** (a stray
  attribute or inline style): every dataclass field becomes an
  attribute unless handled; declare `ARGUMENTS` fully, and use
  `RENAME_ATTRS = {"field": ""}` to suppress a field that is
  configuration rather than markup.
- **It feels like fighting the framework**: check whether
  composition (level 1) around existing components expresses
  the idea; it usually can.

## Related

- [Embed HTML](../add/html.md): the safety rules level 2
  inherits.
- [Developer documentation](../dev/index.md): architecture and
  internals for level 3 and beyond.
