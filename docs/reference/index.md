---
page_type: index
title: Reference
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Find authoritative details fast.
---

# Reference

Exact details, organized for lookup. If you know roughly what you are
looking for, this is the place; if you are still deciding what to add
to your app, start from [Add to Your App](../add/index.md) instead.

## Components

Everything you can put on a page.

- [All components](components/index.md): the master list, grouped by
  purpose, with one line about each.
- [Theme catalog](themes.md): every ready-made look, with the code to
  apply it.

## Core functions and types

The machinery every app uses.

- [route](route.md): the decorator that registers a function as a
  route.
- [Page](page.md): the value a route returns.
- [start_server](start-server.md): the call that starts your app, and
  every option it takes.
- [Site configuration functions](site-config.md): `set_website_title`,
  `set_website_style`, `set_site_information`, and their relatives.

## Partial updates

For apps that change part of a page instead of the whole thing.

- [Fragment](fragment.md): replace one part of the current page.
- [Update](update.md): change state without rendering anything.
- [Redirect](redirect.md): send the visitor to another route.

## Styling and attributes

- [Styling functions](styling-functions.md): every helper that wraps a
  component and returns it styled.
- [Keywords every component accepts](keyword-attributes.md): `style_*`
  keywords, `classes`, `id`, and event handlers.
- [HTML colors](colors.md) and [Fonts](fonts.md): lookup tables for
  color names and safe fonts.

## Testing

- [Testing functions](testing-functions.md): every `assert_` function
  and its options.

## Data types

- [Data types](data-types/index.md): `Picture`, `Photo`, location
  types, file types, and audio types.

## Everything else

- [Glossary](glossary.md): the words Drafter uses, in plain language.
- [Command line](cli.md): flags for running `drafter` from a terminal.
- [Concepts](../concepts/index.md): the explanations behind these
  details, written to be read rather than looked up.
