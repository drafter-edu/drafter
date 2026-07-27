---
page_type: component
title: Page regions
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Section
  - Article
  - Aside
  - Main
  - Nav
  - HeaderContent
  - FooterContent
  - Figure
  - FigureCaption
outcome: Use the semantic page-region components.
---

# Page regions

Group: [Layout](../index.md#layout)

## Description

Nine components name the *regions* of a page: its navigation,
its main content, its sections and asides. They all behave
exactly like [Div](div.md), grouping whatever you put inside,
but the name tells browsers, screen readers, and CSS what each
group *is*. None of them change how anything looks by default;
their value is structure, and structure pays off in
accessibility and styling hooks.

## Syntax

```python
Section(content, more_content, ...)
Nav(Link("Home", "index"), " ", Link("About", "about"))
```

Every member takes any number of content items, like `Div`.

## Parameters

| Component | Names the region for |
| --------- | -------------------- |
| `Main` | The page's primary content, once per page. |
| `Nav` | A cluster of navigation links. |
| `Section` | One thematic section of the page. |
| `Article` | A self-contained piece (a post, a card, an entry). |
| `Aside` | Content beside the point: tips, related links. |
| `HeaderContent` | Introductory content at the top of a page or section. |
| `FooterContent` | Closing content: credits, fine print. |
| `Figure` | An illustration with its caption. |
| `FigureCaption` | The caption inside a `Figure`. |

(`HeaderContent` and `FooterContent` are named to avoid
colliding with [Header](../text/header.md), the heading
component.)

## Examples

```python drafter height=380
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Nav(Link("Home", "index"), " | ", Link("Gallery", "gallery")),
        Main(
            Header("The Daily Babbage"),
            Article(
                Header("Mutt wins hearts at park", 2),
                Paragraph("Witnesses describe the small black dog "
                          "as 'a very good boy'.")
            ),
            Figure(
                "[photo of Babbage looking dignified]",
                FigureCaption("Babbage, moments after the incident.")
            )
        ),
        FooterContent(SmallText("The Daily Babbage is written by pets."))
    ])


@route
def gallery(state: State) -> Page:
    return Page(state, [
        Header("Gallery"),
        Nav(Link("Back home", "index"))
    ])


start_server(State())
```

## Notes

- Structure only: on screen these render like plain groups, and
  that is correct. Add looks with a theme or
  [styling helpers](../../styling-functions.md).
- Screen readers let visitors jump between regions, which is the
  main practical payoff. One `Main` per page, and every cluster
  of links inside a `Nav`, covers most of the benefit.
- These are also clean targets for
  [custom CSS](../../../add/change-appearance/custom-css.md):
  styling `aside` or `.classes` you add beats sprinkling styles
  over individual components.
- `Figure` and `FigureCaption` pair with
  [Image](../media/image.md) for captioned pictures.

## Related components

- [Div (Box)](div.md): the same grouping with no semantic name.
- [Header](../text/header.md): headings, which give regions
  their titles.

## External links

- [Content sectioning on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements#content_sectioning)
