---
page_type: index
title: Concepts
audience: S
priority: P1
prereqs: []
symbols: []
outcome: See how the ideas fit together.
---

# Concepts

The ideas behind Drafter, each explained once, properly. You do not
need to read these in advance; the tutorials and task pages link to
each concept at the moment you have already used it and it deserves a
name. Come here when you want the full story, or the overview.

## The ladder

Each idea builds on the ones above it:

| Concept | In one line | Where you use it |
| ------- | ----------- | ---------------- |
| [How Drafter works](../start/how-drafter-works.md) | Your program runs twice: once to start up and test, then inside the browser as the real app. | Everywhere, quietly |
| [Routes and pages](routes-and-pages.md) | Routes are functions that build and return pages; their names become addresses. | [Add and connect pages](../add/pages.md) |
| [State](state.md) | One dataclass is your app's memory, flowing route to page to route. | [Remember a score or choice](../add/remember-things.md) |
| [Forms and input](forms-and-input.md) | Each input's name fills the route parameter with the same name; annotations convert. | [Ask the user for information](../add/ask-for-information.md) |
| [Dynamic pages](dynamic-pages.md) | One route renders differently from state, data, and arguments. | [Show different content](../add/show-different-content.md) |
| [Live updates](live-updates.md) | Events call routes; routes can replace part of a page instead of all of it. | [Add live behavior](../add/live-behavior.md) |
| [How the web works](how-the-web-works.md) | Browsers, servers, URLs, and where a Drafter app actually runs. | [Deploy and submit](../your-project/deploy/index.md) |

## How these pages relate to the rest of the docs

- The **tutorials** use each idea before naming it, then link here
  from their "Name it" sections.
- The **task pages** in Add to Your App open with working code and
  link here under "Understand it".
- The **reference** states exact behavior without explanation, and
  links here for the why.

If a concept page ever leaves you more confused than you arrived,
that is a documentation bug we want to know about; see
[getting help](../help/index.md).
