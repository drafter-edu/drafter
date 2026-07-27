---
page_type: index
title: Developer documentation
audience: D
priority: P1
prereqs: []
symbols: []
outcome: Orient contributors.
search:
  exclude: true
---

# Developer documentation

This area is for people working on Drafter itself. If you are a
student building an app, you want the
[Reference](../reference/index.md); if you are an instructor, you
want [Teach](../teach/index.md).

## Where to go

- **[Architecture](architecture.md)**: the system design in one
  page: the three run modes, the bridge and client server, and
  how a click becomes a rendered page. The full, authoritative
  version lives in `ARCHITECTURE.md` at the repository root.
- **[Full API reference](#the-api-reference)**: generated
  per-module documentation; see below for how it is built.
- **[Writing documentation](docs-guide.md)**: how to author
  pages for this site, the front-matter schema, runnable fences,
  and the CI gates that check them.
- **[Template zoo](template-zoo.md)**: every design-system
  element rendered with dummy content, for visual review.

Two more pages are planned but not yet written: a contributing
guide (dev setup, test suites, watchers; see the repository
README meanwhile) and an internals map.

## The API reference

The per-module API pages are generated with mkdocstrings from the
source docstrings, and only in full builds:

```console
uv run drafter-docs build --api
```

renders them under `/dev/api/`. Regular development builds skip
them for speed, which is why the section may be absent from a
local preview.

## Ground rules worth knowing

- The student-facing docs never show dicts, comprehensions,
  lambdas, or exceptions; developer docs have no such limit.
- `docs_legacy/` is mining material from the old site, not part
  of the build.
- Skulpt is a legacy engine: its code and its known-failing test
  suite are outside the validation baseline and should not be
  modified as a side effect of other work.
