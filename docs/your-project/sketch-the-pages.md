---
page_type: how-to
title: Sketch the pages
level: L2
audience: S
priority: P1
prereqs: [your-project/choose-an-idea]
symbols: []
outcome: Draw the app before coding it.
---

# Sketch the pages

## Goal

You want a drawing of every page and every connection before you
write a line of code, because pages are cheap on paper and
expensive in an editor.

## Before you start

You have [an idea and a shape](choose-an-idea.md). You need paper
(or a whiteboard, or a tablet); this step is deliberately not done
in Python.

## Step 1: One box per page

Draw a rough rectangle for each page and give it a lowercase,
code-ready name: `index`, `add_entry`, `history`. These names will
become your route functions, so choosing them now is real work,
not decoration. Inside each box, scribble what the page shows: a
title, the main content, and every button or link.

Keep the set small. Most course projects want three to five pages;
if you have drawn eight, some of them are probably
[one dynamic page](../concepts/dynamic-pages.md) in disguise (a
"scene 1" and "scene 2" box are one `scene` route fed by data).

## Step 2: Arrows for every click

Draw an arrow from every button and link to the page it leads to.
Label the arrow with the button's text. When an arrow's destination
depends on something ("Submit goes to the receipt, unless the cart
is empty"), draw both arrows and note the condition; that
condition will become an `if` in a route.

A tracker's map might come out like this:

```text
            "Add an entry"
  index ────────────────────▶ add_entry
    ▲  ◀──────────────────────── │
    │       "Save" / "Cancel"
    │ "See history"
    ▼
  history ──"Back"──▶ index
```

## Step 3: Walk the paths

Play user with a pencil: start at `index` and follow arrows through
every task your one-liner promises. Three checks, each catching a
classic flaw:

- **Can you get everywhere?** A page with no arrows *in* is
  unreachable except by address.
- **Can you always get back?** A page with no arrows *out* is a
  dead end; add a way home.
- **Does every form's arrow land on a page that shows the result?**
  Submitting and seeing nothing change feels broken even when it
  worked.

## Step 4: Mark what varies

Circle everything on the sketches that changes while the app runs:
the count that grows, the list that fills, the name that appears
after a form. These circles are the input to
[deciding what to remember](plan-your-data.md); everything circled
must live in state, and everything not circled is just page
furniture.

## Common problems

- **Sketching screens, not flows**: a beautiful drawing of one page
  is a poster, not a plan. The arrows are the plan.
- **Perfectionism**: boxes and scribbles, ten minutes, done. If it
  takes an hour, you are drawing the product instead of the map.
- **A page you cannot name**: if no honest lowercase name fits
  ("misc_stuff"), the page is probably two pages, or none.
- **Skipping this because the app is small**: small apps grow. The
  sketch is the cheapest insurance you will ever buy.

## You are ready for the next step when

Every page has a name, every click has an arrow, the walk-through
finds no dead ends, and the changing parts are circled. Take the
sketch to [Decide what to remember](plan-your-data.md).
