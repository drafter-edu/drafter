---
page_type: reference
title: Glossary
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Look up terms in stable, plain language.
---

# Glossary

The words these docs use, each with its plain meaning and a link to
the page that tells the whole story. The docs use these words
consistently, so if a sentence confuses you, the confusing word is
probably here.

**argument**: An extra value a button or link carries to its route, filling a
  parameter by name. In wider Python, "argument" also means any
  value passed to a function; Drafter's
  [Argument](components/actions/argument.md) component is the
  page-sized version of the same idea.

**component**: Anything you can put in a page's content list besides a plain
  string: buttons, text boxes, images, tables. The
  [full list](components/index.md).

**dataclass**: A Python class defined with `@dataclass`, used as a labeled bundle
  of values. Your `State` is one; so is each record in a list like
  the [pet registry's](../examples/pet-registry.md) pets.

**debug panel**: The tool strip Drafter shows under your app while you develop:
  current state, page history, tests, and more.
  [Tour](../start/debug-panel.md); [in depth](../help/debug-panel.md).

**deploy**: To turn your project into a public website with a real address, by
  having GitHub Pages build and host it.
  [The arc](../your-project/deploy/index.md).

**event**: Something the visitor does that a component can react to by
  calling a route: typing, choosing, hovering, clicking.
  [Live updates](../concepts/live-updates.md).

**fragment**: A route's answer that replaces one part of the page instead of all
  of it. [Fragment](fragment.md).

**page**: What a route returns: the state to carry forward plus the list of
  content to show. Also, loosely, the thing the visitor sees.
  [Page](page.md).

**parameter**: A name in a function's `def` line that receives a value. Route
  parameters are filled by state, form fields, and arguments, by
  name. [Forms and input](../concepts/forms-and-input.md).

**production**: The finished, public version of your app: titled, styled, debug
  panel hidden. The opposite of "while you are developing".
  [Prepare for release](../your-project/deploy/prepare.md).

**regression test**: A test that protects something that already works from being
  broken by later changes.
  [Freeze finished pages](../add/freeze-pages.md).

**render**: To turn your page description into the actual pixels-and-HTML the
  browser shows. Drafter renders the page a route returns.

**route**: A function marked with `@route` that builds and returns a page.
  Routes are not pages; they are the recipes that produce them, and
  their names become addresses.
  [Routes and pages](../concepts/routes-and-pages.md).

**server**: The program that answers a browser's requests. During development
  that role is played on your computer; after loading a deployed
  Drafter app, your own program plays it from inside the browser
  tab. [How Drafter works](../start/how-drafter-works.md).

**state**: Your app's memory: one value, almost always a dataclass, passed to
  every route and carried by every page. Lost on reload, on purpose.
  [State](../concepts/state.md).

**theme**: A ready-made look for the whole site, applied by name with one
  line. [Catalog](themes.md).

**URL**: A web address: which server to ask and what to ask for. Route
  names become the path part of your app's URLs.
  [How the web works](../concepts/how-the-web-works.md).

## Words these docs avoid

A few terms you will meet elsewhere, mapped to what the docs say
instead: a *view* or *handler* is a **route**; a *model* is your
**State**; *the front end* is the whole app, since Drafter has no
back end; *widgets* or *elements* are **components**.
