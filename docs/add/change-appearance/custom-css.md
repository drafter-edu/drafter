---
page_type: how-to
title: Custom CSS
level: L3
audience: S
priority: P1
prereqs: [add/change-appearance/helpers]
symbols: []
outcome: Use real CSS with classes.
---

# Custom CSS

## Goal

Styling components one at a time is getting repetitive. You want to
write a rule once and have it apply everywhere.

## Before you start

You know the [box and its properties](design-basics.md), and you have
set them with [styling functions and keywords](helpers.md).

## You already write properties and values

Here are three notices, with the same two keywords typed three times:

```python
Div("The bake sale moved to Saturday.",
    style_border="2px solid slateblue",
    style_padding="12px")
Div("Captain the cat has opinions.",
    style_border="2px solid slateblue",
    style_padding="12px")
Div("Bring a raincoat.",
    style_border="2px solid slateblue",
    style_padding="12px")
```

A CSS rule says it once. The properties and values are the ones you
know, and the new part is the first line, which says who gets them:

```css
.notice {
    border: 2px solid slateblue;
    padding: 12px;
}
```

## The parts of a rule

Every rule answers three questions:

<div class="drafter-rule">
<pre class="drafter-rule__code" role="img" aria-label="A CSS rule. The selector is .notice. Inside curly braces are two lines: the property border with the value 2px solid slateblue, and the property padding with the value 12px. Each line has a colon between the property and the value, and ends with a semicolon."><span class="drafter-rule__selector">.notice</span> {
    <span class="drafter-rule__property">border</span>: <span class="drafter-rule__value">2px solid slateblue</span>;
    <span class="drafter-rule__property">padding</span>: <span class="drafter-rule__value">12px</span>;
}</pre>
<div class="drafter-rule__parts">
<div class="drafter-rule__part drafter-rule__part--selector"><b>Selector</b>Who gets styled?</div>
<div class="drafter-rule__part drafter-rule__part--property"><b>Property</b>What are you changing?</div>
<div class="drafter-rule__part drafter-rule__part--value"><b>Value</b>How should it look?</div>
</div>
</div>

Four symbols hold a rule together. Curly braces `{` `}` wrap the
rule's lines, a colon separates each property from its value, and a
semicolon ends every line.

## A tag selector styles every component of one kind

`add_website_css` adds a rule to the whole site. Each component
becomes a tag in the page: a `Button` is a `button`, a `Link` is an
`a`, and a `Header` is an `h1`. When the selector is a tag name, every
component of that kind gets the rule:

```python drafter hl_lines="3-9" height=260
from drafter import *

add_website_css("""
button {
    background-color: lavender;
    border: 2px solid slateblue;
    padding: 8px 16px;
}
""")


@route
def index() -> Page:
    return Page([
        Header("Lavender World"),
        Button("Every button", "index"),
        Button("Gets the rule", "index")
    ])


start_server()
```

## A class selector styles the components you choose

A class is a name you make up and hand out. The `classes` keyword
puts the name on a component, and a selector that starts with a dot
finds every component carrying it. The dot goes in the CSS and never
in the Python:

```python drafter hl_lines="4 15-16" height=260
from drafter import *

add_website_css("""
.notice {
    border: 2px solid slateblue;
    padding: 12px;
    margin: 8px 0;
}
""")


@route
def index() -> Page:
    return Page([
        Div("The bake sale moved to Saturday.", classes="notice"),
        Div("Captain the cat has opinions.", classes="notice"),
        "Plain text stays plain."
    ])


start_server()
```

## Tag or class?

A tag rule is a decision about the whole site: every button, every
header. A class is a name you hand out, so you decide who is in. One
class can go on many components, and one component can carry several
classes, separated by spaces.

| Selector | Looks like | Who gets styled |
| -------- | ---------- | --------------- |
| Tag | `button` | Every `Button` on the site |
| Class | `.notice` | Each component with `classes="notice"` |

Prefer a class for anything less than a sitewide decision.

## Common problems

- **`add_website_css("style.css")` complains**: that function takes
  CSS, not a file name. Use `add_website_css_file("style.css")` to
  link a file.
- **The rule does nothing**: check the selector against what is
  actually rendered. `classes="notice"` pairs with `.notice` (the
  dot belongs in the selector, not in the keyword). Then check the
  four symbols: a misspelled selector, a missing brace, or a missing
  semicolon fails silently.
- **The rule styles too much**: `button` styles every button,
  including ones you forgot about. Switch to a class.

For a rule that a theme overrides, or a selector that reaches
Drafter's own interface, see [Styling gotchas](gotchas.md).

## In more depth

### A shorthand for one rule

`add_website_css` also takes the selector and the lines that go inside
the braces as two separate arguments, and adds the braces for you.
These two calls do the same thing:

```python
add_website_css(".notice { border: 2px solid navy; }")
add_website_css(".notice", "border: 2px solid navy;")
```

With one argument, you are handing over raw CSS, which can contain
several rules at once. With two, the first is the selector and the
second is the lines that belong inside the braces.

### Keep the CSS in its own file

Once you have more than a few rules, a separate `style.css` file next
to your program is easier to edit, and your editor will highlight it
properly. The rules are written exactly as they are inside
`add_website_css`, and `add_website_css_file` links the file into
every page:

```python
from drafter import *

add_website_css_file("style.css")
```

```css
/* style.css, saved in the same folder as your program */
.notice {
    border: 2px solid darkslateblue;
    border-radius: 8px;
    padding: 12px;
}
```

The argument can also be a full URL, such as a stylesheet from a
font service. When you name a file, Drafter checks that it exists as
soon as the line runs; a typo like `"styles.css"` for `style.css`
produces an error that suggests the right name instead of silently
doing nothing. The file is remembered for deployment too, so it is
copied into the built site.

The same pair exists for JavaScript: `add_website_js` for code written
in your program, `add_website_js_file` for a `.js` file or URL.

### Two more selectors

Tags and classes cover most rules. Two other kinds of selector are
worth knowing:

| Selector | Applies to | Example |
| -------- | ---------- | ------- |
| `.a .b` | Things with the class `b` inside things with the class `a` | `.card .title` |
| `#name` | The one component with `id="name"` | `#scoreboard` |

To find which tag a component renders as, check the "External links"
section of its reference page.

### Style tags inside a page

CSS from `add_website_css` applies to the whole site. When only one
page needs a rule, the `Page`'s `css` parameter attaches the rule
to that page alone. This is an advanced feature documented on
[Page](../../reference/page.md).

### Where this sits with themes

Themes are CSS too, and they load before yours, so your rules
usually win when they target the same element precisely. A strongly
opinionated theme can still override you; when your rule seems to
be ignored, see the [specificity gotcha](gotchas.md). To build a
look entirely your own, start from `set_website_style("none")`, the
blank slate.

Broad selectors like `body` also reach Drafter's own interface,
including the debug panel. Target your content instead; the
[gotchas page](gotchas.md) names the right container.

## Understand it

[Design basics](design-basics.md) explains the box and the properties
a rule sets. Selectors are the only new machinery on this page.

## See another example

The [styling playground](../../examples/playground/styling.md) has
the three ways to style a site side by side, cards included.

## Look it up

[add_website_css](../../reference/site-config.md#add_website_css),
[add_website_css_file](../../reference/site-config.md#add_website_css_file),
and [classes](../../reference/keyword-attributes.md).

## Fix a problem

[Styling gotchas](gotchas.md) collects the surprising parts of
styling in one place.
