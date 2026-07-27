---
page_type: how-to
title: Classroom logistics
audience: T
priority: P2
prereqs: []
symbols: []
outcome: Run Drafter robustly in class.
search:
  exclude: true
---

# Classroom logistics

## Goal

Run Drafter sessions that survive contact with lab machines,
conference wifi, and a projector, and grade the results without
opening sixty editors. Practical notes only; the pedagogy lives
in [Why Drafter](why-drafter.md) and the
[lesson plans](lesson-plans/index.md).

## Before you start

Know your room: whether students bring machines or use lab
ones, whether an installation is centrally managed, and what
the network blocks. Every contingency below is cheap the week
before and expensive live.

## Installations

- **Lab machines**: preinstall Drafter (`pip install drafter`)
  in the image, and preload the browser engine once per image by
  running any example and opening the app; that caches the
  Pyodide download so first-day sessions skip the big fetch.
- **Student machines**: assign
  [Get Drafter running](../start/install.md) *before* the first
  session, with a verification step
  (`python -c "import drafter"`) students screenshot. Expect a
  tail of Thonny path issues; office hours absorb them better
  than class time.
- **Version pinning**: for a term, pinning
  (`pip install drafter==X.Y`) beats surprises; upgrade between
  terms, not weeks.

## The network contingency

The one dependency worth planning around: the first load of an
app fetches Pyodide from a CDN, once per browser cache.

- Warm the cache the session before you need it (any Drafter
  app opened once does it).
- On restricted networks, test early whether the CDN is
  reachable; `--pyodide-url` can point at an allowed mirror or
  a locally served copy.
- Map imagery ([Map](../reference/components/place/map.md))
  needs the network live, every time; demos that must not fail
  offline should not be map demos.
- Full offline plan: a warmed cache plus bundled examples keeps
  a session alive with no connectivity at all, and the paper
  [sketching exercises](../your-project/sketch-the-pages.md)
  are the zero-tech fallback.

## Projector setup

- High-contrast themes read best from the back row; `"98"` and
  `"terminal"` project famously, `"brutal"` is loud but legible,
  and the [catalog](../reference/themes.md) previews all of
  them.
- Bump the browser zoom before class, not during.
- Keep the debug panel visible while teaching: watching state
  change in the Current tab is half the pedagogy of the
  [big ideas](big-ideas.md).

## Grading mechanics

- **Deployed URL as the submission.** The
  [deploy guide](../your-project/deploy/index.md) makes a live
  URL a fair requirement, and grading from URLs needs no
  environment setup.
- **The about page.** `set_site_information` bakes author,
  description, and planning links into the deployed site's
  about page, so provenance travels with the submission; the
  builder warns when it was never called.
- **Tests as evidence.** Requiring one assertion per feature
  (the [testing lab](lesson-plans/testing-lab.md)'s habit)
  means the Tests tab shows a feature checklist on arrival.
- **Rubric starting point**: 40% features work as specified, 20%
  tests honest and passing, 15% state design fits the data, 15%
  interface quality (labels, empty states, no fake security
  claims), 10% deployment and about-page completeness. Adjust
  freely; the categories matter more than the weights.
- **Late-breaking "it worked locally"**: nearly always a
  [missing bundled asset](../help/errors/missing-asset-on-deploy.md)
  or a deploy workflow that never ran; the
  [deploy troubleshooting](../your-project/deploy/troubleshooting.md)
  page settles it, and partial credit for a working local app
  with a broken deploy is worth deciding in advance.

## Common problems

- **The first-day fetch melts the wifi**: thirty simultaneous
  Pyodide downloads is real traffic; warm caches beforehand, or
  stagger the first run.
- **A student's app runs but the projector demo will not**:
  usually an extension-laden browser profile; keep a clean
  browser profile for projecting.
- **Lab policies block localhost ports**: `--port` picks
  another; genuinely blocked localhost is rare but discovering
  it live is memorable in the wrong way, so test one machine
  early.
- **Students confuse the framed dev view with the deployed
  look**: show `--production` once so they see what graders and
  families will see.

## Related

- [Lesson plans](lesson-plans/index.md): the sessions these
  logistics serve.
- [Project ideas](project-ideas.md): assignments the rubric
  fits.
