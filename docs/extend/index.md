---
page_type: index
title: Extend
level: L4
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Orient advanced students.
---

# Extend

Most Drafter projects never need anything on these pages. They
exist for the moment your project bumps into the edge of the
usual toolkit: you want a library the examples never mention, you
are curious how Python runs in a browser at all, or you need to
know precisely what is and is not protected before you build
something login-shaped.

## The pages

- **[Python in the browser](pyodide.md)**: how your program
  actually runs (Pyodide and WebAssembly), why the first load is
  slow, and what the in-browser filesystem really is. Start here;
  the other pages lean on it.
- **[Third-party libraries](packages.md)**: using matplotlib,
  pandas, requests, and other packages, what loads automatically,
  and what cannot work in a browser.
- **[Deploy with GitHub Actions](github-actions.md)**: build the
  deployment machinery yourself, from an empty repository to a
  site that republishes on every push.
- **[Security honestly](security.md)**: exactly which protections
  exist (very few), why that is fine for course projects, and
  what would require a real backend.
- **[JavaScript interop](javascript.md)**: the `js` module and
  the other doors to the browser, for the feature no component
  covers.
- **[Build your own components](custom-components.md)**: three
  levels of packaging repeated page furniture, from helper
  functions to the `RenderPlan` API.
- **[Performance](performance.md)**: the four real causes of a
  slow Drafter app, and what fixes each.
- **[Moving on to Flask](flask.md)**: the bridge to a backend
  framework, once your project needs what Drafter deliberately
  lacks.

## Fair warning

Pages here relax the rules the rest of the student docs follow:
you may meet dictionaries, exceptions, and other Python your
course has not covered. Each page marks those moments, but if
something reads as unfamiliar, that is why, and it is safe to
walk away until you need it.
