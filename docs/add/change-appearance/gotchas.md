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

The corners of styling where Drafter's structure or CSS's rules
produce surprises. Each entry: the surprise, the reason, the fix.

## Styling `body` styles the debug panel too

`add_website_css("body", ...)` looks like "style my app", but the
page's real body contains everything: your content *and* Drafter's
frame, footer, and debug panel. Your app's content lives inside a
container with the id `drafter-body--`, so target that instead:

```python
add_website_css("#drafter-body--", "font-family: Georgia;")
add_website_css("#drafter-body-- h1", "color: darkslateblue;")
```

(Drafter's own elements all carry the trailing double hyphen, which
marks them as internal; leave those alone otherwise.)

## The theme is overriding your CSS

Themes are stylesheets with opinions, and some state those opinions
forcefully enough that your rule loses the specificity contest even
though yours loaded later. Escapes, in escalating order:

1. Make your selector more specific:
   `#drafter-body-- button` beats `button`.
2. Pick a quieter theme; `simple`, `sakura`, and `water` impose
   less.
3. Go to `set_website_style("none")` and own every pixel yourself.

Confirm what is actually winning with the browser's inspector
(right-click the element, Inspect): the styles panel shows every
rule that applies, with the losers struck through.

## The window frame is part of what you see

During development your app sits inside Drafter's frame, which caps
its width; a "full-width" design will not look full-width until you
turn the frame off with `set_website_framed(False)`. The frame is
also skipped entirely on deployed sites that turn it off in
[release prep](../../your-project/deploy/prepare.md), so judge
full-page layouts with the frame off, not on.

## Styles your tests cannot see

Assertions ignore styling by default, and even
[assert_style](../../reference/testing-functions.md#assert_style)
only sees styles set *on the component*, via helpers, `style_*`
keywords, or `update_style`. Styles that arrive from a theme or an
`add_website_css` rule are invisible to it; there is no assertion
that computes what the browser finally renders. Test the styles you
set directly, and judge sheet-applied styling with your eyes.

## Two styling systems, one element

Wrapping a component with a helper and also giving it a `style_*`
keyword both write inline styles, and the later write wins when
they touch the same property. Mixing is fine; just remember that
`change_color(Button("Go", "index", style_color="red"), "blue")`
has one winner, and it is the helper that ran last.

## When your CSS and someone else's page fight

Embedding your app somewhere with its own aggressive CSS (or
running several apps on one page, as these docs do) can produce
cross-contamination. The heavy shield is the `--use-shadow-dom`
command-line flag, which isolates the app's styles from the page
around it. You will likely never need it for your own project; it
exists for embedders.

## Still surprised?

The browser inspector answers most "why does it look like that?"
questions: it shows the element, every rule applied to it, and lets
you edit values live before touching your code. For problems beyond
styling, start at [Troubleshooting](../../help/troubleshooting.md).
