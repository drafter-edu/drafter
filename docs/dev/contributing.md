---
page_type: how-to
title: Contributing
audience: D
priority: P2
prereqs: []
symbols: []
outcome: Set up and validate a development environment.
search:
  exclude: true
---

# Contributing

## Goal

Go from a fresh clone to a validated development environment:
able to run an example against your local code, run every test
suite, and build these docs. The repository `README.md` is the
authority when details drift; this page is the tour.

## Before you start

You need Python 3.10+ (3.11+ recommended), Node.js 18+ with
npm, and [uv](https://github.com/astral-sh/uv). Development
happens on the `v2-pyodide` branch.

## Setup

```console
git clone https://github.com/drafter-edu/drafter.git
cd drafter
git checkout v2-pyodide
uv sync
cd js
npm install
cd ..
```

`uv sync` builds the Python environment from the lockfile;
`npm install` readies the TypeScript toolchain. Confirm life
with an example:

```console
uv run examples/shop.py
```

The `examples/` directory is full of small apps exercising
individual features, and running one against your working copy
is the fastest smoke test there is.

## Where things live

- `src/drafter/`: the Python package (components, payloads,
  router, client server, bridge, builder, configuration). The
  [internals map](internals-map.md) breaks this down module by
  module.
- `js/`: the TypeScript client (bridge, debug panel, custom
  elements, engine bootstrap), built with tsup into `js/dist/`.
- `tests/` and `js/src/__tests__/`: the Python and JS suites.
- `docs/`: this documentation; `docs_legacy/` is the retired v1
  site kept as source material, not built.
- `Justfile`: the dev recipes; `just --list` shows them.

Wheels bundle `js/dist/` into the package at build time, so the
JS must be built before packaging.

## Iterating on the JS client

Two watchers make TypeScript edits flow into a running app:

```console
cd js
npm run dev
```

rebuilds the bridge on every save, and the dev server's file
watcher reloads connected browsers. Run your test app
(`uv run examples/simplest.py`) in another terminal and edit
away. (`npm run precompile:watch` is the Skulpt equivalent,
only needed when touching that legacy path.)

## Validating

```console
uv run pytest
cd js
npm run test
npm run test:integration
```

or everything at once, formatting and linting included:

```console
just validate
```

Two standing rules:

- The baseline is green: every Python test and every default JS
  test passes on `v2-pyodide`, and changes keep it that way.
- `npm run test:skulpt` is known-failing legacy and outside the
  baseline; do not run, fix, or modify Skulpt code as a side
  effect of other work.

## Docs

```console
uv run drafter-docs serve
uv run drafter-docs build --strict
```

The strict build is what CI runs, together with the docs linter,
manifest check, and fence-execution tests.
[Writing documentation](docs-guide.md) covers authoring pages
that pass all four.

## Common problems

- **An example serves stale JS**: the watcher was not running
  when you edited; `npm run dev` (or a one-shot
  `npm run build`) refreshes `js/dist/`.
- **Python tests pass, JS integration tests time out**: the
  integration suite boots real Pyodide with a large heap and
  runs serially; give it time and memory, and run the fast
  `npm run test` while iterating.
- **`drafter-docs` cannot compile embedded demos against your
  local changes**: use `--dev`, which switches the demo
  compiler to the locally built package.
- **A docs page fails CI mysteriously**: the linter's rules
  (front-matter, required sections, fence tags) are all
  documented in [Writing documentation](docs-guide.md).

## Related

- [Architecture](architecture.md): how the pieces fit.
- [Internals map](internals-map.md): which module to open.
