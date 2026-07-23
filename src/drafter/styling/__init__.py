"""Styling support for Drafter pages.

Contains two modules:

- `styling`: student-facing helper functions (`bold`, `change_color`,
  `update_style`, ...) that update a component's CSS styles or HTML
  attributes and return the component so calls can be chained inline.
- `themes`: the `Theme` and `ThemeSystem` classes and the shared
  `theme_system` instance that manage the site-wide visual themes
  selectable with `set_website_style`.
"""
