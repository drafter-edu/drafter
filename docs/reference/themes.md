---
page_type: reference
title: Theme catalog
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Preview and choose among all 20 themes.
---

# Theme catalog

Every theme, live. Each preview below is the same tiny app with one
line changed:

```python
set_website_style("terminal")
```

Pick by browsing, then write the name into your own
`set_website_style(...)` call; the how-to is
[Use a theme](../add/change-appearance/themes.md). Each preview is
editable, so you can add your own content to see how it dresses up.
The debug panel's theme switcher is the other quick way to compare
themes on your real app.

Credit where due: most themes are ports of open-source classless
stylesheets, linked from each entry.

## default

The style you get without choosing. Clean and unobtrusive.

```python drafter height=340
from drafter import *

set_website_style("default")


@route
def index() -> Page:
    return Page([
        Header("The default theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## none

A blank slate for [custom CSS](../add/change-appearance/custom-css.md).

```python drafter height=340
from drafter import *

set_website_style("none")


@route
def index() -> Page:
    return Page([
        Header("The none theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## almond

Soft, warm, and rounded. Based on [Almond.CSS by Alvaro Montoro](https://github.com/alvaromontoro/almond.css).

```python drafter height=340
from drafter import *

set_website_style("almond")


@route
def index() -> Page:
    return Page([
        Header("The almond theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## brutal

Thick borders and hard shadows, loudly retro. Based on [Brutal by Vitor Estevam](https://github.com/VitorEstevam/Brutal).

```python drafter height=340
from drafter import *

set_website_style("brutal")


@route
def index() -> Page:
    return Page([
        Header("The brutal theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## daub

Hand-drawn, sketchy strokes. Based on [Daub UI Kit by Sliday](https://github.com/sliday/daub/tree/main).

```python drafter height=340
from drafter import *

set_website_style("daub")


@route
def index() -> Page:
    return Page([
        Header("The daub theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## latex

Looks like a typeset academic paper. Based on [LaTeX.css by Vincent Doerig](https://latex.vercel.app/).

```python drafter height=340
from drafter import *

set_website_style("latex")


@route
def index() -> Page:
    return Page([
        Header("The latex theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## magick

Serif charm with a spellbook feel. Based on [Magick.css by winterveil](https://github.com/wintermute-cell/magick.css).

```python drafter height=340
from drafter import *

set_website_style("magick")


@route
def index() -> Page:
    return Page([
        Header("The magick theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## mvp

Plain, professional, presentation-ready. Based on [MVP.css by andybrewer](https://andybrewer.github.io/mvp/).

```python drafter height=340
from drafter import *

set_website_style("mvp")


@route
def index() -> Page:
    return Page([
        Header("The mvp theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## pico

Modern and polished, with generous spacing. Based on [Pico CSS](https://picocss.com/).

```python drafter height=340
from drafter import *

set_website_style("pico")


@route
def index() -> Page:
    return Page([
        Header("The pico theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## retro

Chunky headers and old-web energy. Based on [retro (markdowncss) by John Otander](https://github.com/markdowncss/retro).

```python drafter height=340
from drafter import *

set_website_style("retro")


@route
def index() -> Page:
    return Page([
        Header("The retro theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## sakura

Minimal and quiet, with a hint of pink. Based on [Sakura by oxal](https://oxal.org/projects/sakura/).

```python drafter height=340
from drafter import *

set_website_style("sakura")


@route
def index() -> Page:
    return Page([
        Header("The sakura theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## simple

Understated and highly readable. Based on [Simple.css by kevquirk](https://simplecss.org/).

```python drafter height=340
from drafter import *

set_website_style("simple")


@route
def index() -> Page:
    return Page([
        Header("The simple theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## skeleton

Light, airy, grid-friendly. Based on [Skeleton by Dave Gamache](http://getskeleton.com/).

```python drafter height=340
from drafter import *

set_website_style("skeleton")


@route
def index() -> Page:
    return Page([
        Header("The skeleton theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## tacit

Spartan and tidy. Based on [Tacit by yegor256](https://yegor256.github.io/tacit/).

```python drafter height=340
from drafter import *

set_website_style("tacit")


@route
def index() -> Page:
    return Page([
        Header("The tacit theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## terminal

Dark monospace, like a command line. Based on [Terminal theme by panr (Radek Koziel)](https://github.com/panr/hugo-theme-terminal).

```python drafter height=340
from drafter import *

set_website_style("terminal")


@route
def index() -> Page:
    return Page([
        Header("The terminal theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## water

A comfortable dark mode with no fuss. Based on [Water.css (dark) by Kognise](https://watercss.kognise.dev/).

```python drafter height=340
from drafter import *

set_website_style("water")


@route
def index() -> Page:
    return Page([
        Header("The water theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## yorha

Beige-and-brown sci-fi menus. Based on [YoRHa CSS by Ethan Chan](https://metakirby5.github.io/yorha/).

```python drafter height=340
from drafter import *

set_website_style("yorha")


@route
def index() -> Page:
    return Page([
        Header("The yorha theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## 98

A 1998 operating system, pixel borders and all. Based on [98.css by jdan](https://jdan.github.io/98.css/).

```python drafter height=340
from drafter import *

set_website_style("98")


@route
def index() -> Page:
    return Page([
        Header("The 98 theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## xp

A 2001 operating system, glossy blue. Based on [XP.css by botoxparty](https://botoxparty.github.io/XP.css/).

```python drafter height=340
from drafter import *

set_website_style("xp")


@route
def index() -> Page:
    return Page([
        Header("The xp theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## 7

A 2009 operating system, gradients and glass. Based on [7.css by khang-nd](https://khang-nd.github.io/7.css/).

```python drafter height=340
from drafter import *

set_website_style("7")


@route
def index() -> Page:
    return Page([
        Header("The 7 theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
```

## Related

- [Use a theme](../add/change-appearance/themes.md): applying a theme
  and combining it with your own styling.
- [Site configuration functions](site-config.md): `set_website_style`
  and its relatives.
- [Custom CSS](../add/change-appearance/custom-css.md): start from
  `none` and build your own look.
