---
page_type: troubleshooting
title: Styling gotchas
level: L3
audience: S
priority: P1
prereqs: [add/change-appearance/custom-css]
symbols: []
outcome: Avoid the weird parts of styling a Drafter page.
---

# Styling gotchas

This page collects the corners of styling where Drafter's structure
or CSS's rules produce surprises. Each entry describes the
surprise, the reason for it, and the fix.

## Styling `body` styles the debug panel too

`add_website_css("body", ...)` looks like "style my app", but the
page's real body contains everything: your content *and* Drafter's
frame, footer, and debug panel. Your app's content lives inside a
container with the id `drafter-body--`, so target that instead:

```python
add_website_css("#drafter-body--", "font-family: Georgia;")
add_website_css("#drafter-body-- h1", "color: darkslateblue;")
```

(Drafter's own elements all carry a trailing double hyphen, which
marks them as internal. Apart from targeting `#drafter-body--`,
leave them alone.)

## The theme is overriding your CSS

Some themes write their rules with enough specificity that your
rule loses the contest even though it loaded later. There are three
ways out, in escalating order:

1. Make your selector more specific:
   `#drafter-body-- button` beats `button`.
2. Pick a quieter theme; `simple`, `sakura`, and `water` impose
   fewer rules.
3. Switch to `set_website_style("none")` and write every style
   yourself.

Confirm which rule is actually winning with the browser's inspector
(right-click the element, then choose Inspect): the styles panel
shows every rule that applies, with the overridden ones struck
through.

## The window frame is part of what you see

During development, your app sits inside Drafter's frame, which
caps its width. A design meant to fill the window will not look
full-width until you turn the frame off with
`set_website_framed(False)`. Deployed sites that turn the frame off
during [release prep](../../your-project/deploy/prepare.md) do not
show it at all, so judge full-page layouts with the frame off, not
on.

## Styles your tests cannot see

Assertions ignore styling by default, and even
[assert_style](../../reference/testing-functions.md#assert_style)
only sees styles set *on the component*, via helpers, `style_*`
keywords, or `update_style`. Styles that arrive from a theme or an
`add_website_css` rule are invisible to it, and there is no
assertion that computes what the browser finally renders. Test the
styles you set directly, and judge sheet-applied styling with your
eyes.

## Two styling systems, one element

Wrapping a component with a helper and also giving it a `style_*`
keyword both write inline styles, and when they touch the same
property, the later write wins. Mixing them is fine; remember that
`change_color(Button("Go", "index", style_color="red"), "blue")`
has one winner, and it is the helper, because it ran last.

## When your CSS and someone else's page fight

Embedding your app somewhere with its own aggressive CSS (or
running several apps on one page, as these docs do) can produce
cross-contamination. The strongest protection is the
`--use-shadow-dom` command-line flag, which isolates the app's
styles from the page around it. You will probably never need it for
your own project; it exists for sites that embed Drafter apps.

## Still surprised?

The browser inspector answers most "why does it look like that?"
questions: it shows the element, every rule applied to it, and lets
you edit values live before touching your code. For problems beyond
styling, start at [Troubleshooting](../../help/troubleshooting.md).
