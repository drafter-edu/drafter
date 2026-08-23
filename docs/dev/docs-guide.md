---
page_type: how-to
title: Writing documentation
audience: D
priority: P1
prereqs: []
symbols: []
outcome: Author pages that pass documentation CI.
search:
  exclude: true
---

# Writing documentation

## Goal

You want to add or edit a page on this documentation site and have it pass
the documentation CI gates on the first try.

## Before you start

You can build the site locally:

- `uv run drafter-docs serve --dev` — live-reloading local build.
- `uv run drafter-docs build --strict` — the CI build; must pass with no
  warnings.
- `uv run drafter-docs build --api` — also renders the full `/dev/api/`
  reference (slow; skipped by default).

The site follows the plan in `STUDENT_DOCS_PLAN.md` at the repository
root; nearly all planned pages are written, with new pages scaffolded as
stubs from `tools/docs_manifest.yaml`. The old site content lives in
`docs_legacy/` as source material for the rewrite and is not built.

## The URL contract

`tools/docs_manifest.yaml` is the authoritative sitemap. To add a page:

1. Add its entry to the manifest (path, title, template, level, audience,
   priority, outcome, symbols).
2. Run `uv run python tools/scaffold_docs.py` to generate the stub.
3. Add it to `nav:` in `mkdocs.yml`.
4. Write the content, then delete the `status: stub` line.

The linter fails on any page in `docs/` that is not in the manifest, and on
any manifest entry with no page.

## Front-matter schema

Every page begins with YAML front-matter:

```yaml
page_type: how-to        # template name; see the list below
title: Ask the user for information
level: L2                # L1-L4; omit for unleveled pages (indexes)
audience: S              # S students, T teachers, D developers
priority: P0             # P0 minimum pathway, P1 first release, P2 later
prereqs: []              # slugs of pages the reader should have seen
symbols: []              # drafter API names this page primarily documents
outcome: Build working forms.
status: stub             # delete this line when the page is written
```

Notes:

- The key is `page_type`, not `template` — MkDocs reserves the `template`
  front-matter key for overriding a page's Jinja template.
- Teach and Developer pages also carry `search: {exclude: true}` so they
  stay out of the student search index.
- Error entries (`page_type: error`) must carry `error_text`: the exact
  technical error string the entry documents. The fence harness checks
  repro fences against it.
- `symbols` drives the coverage gate: every name in `drafter.__all__` must
  appear in some page's `symbols` or in
  `tools/docs_coverage_exclusions.yaml` with a reason.

Page types: `tutorial`, `concept`, `how-to`, `component`, `api`, `example`,
`error`, `gallery`, `lesson`, `misconception`, `archetype`, plus the
structural types `index`, `reference`, `troubleshooting`, `playground`.
Non-stub pages must contain the sections their type requires (see
`REQUIRED_HEADINGS` in `tools/docs_lint.py`, which implements
STUDENT_DOCS_PLAN.md §7).

## Runnable fences

Embedded demos are ordinary fenced code blocks marked with `drafter`:

````markdown
```python drafter hl_lines="2-4" height=300
from drafter import *
start_server()
```
````

- The drafter-codeblocks plugin compiles each one into a sandboxed iframe
  at build time; a compile failure fails the build.
- `hl_lines` highlights lines in the rendered source; `height` overrides
  the iframe height. These are the only fence parameters the plugin knows.
- Tutorial step listings use `hl_lines` to mark the lines that are new or
  changed since the previous step's listing, so repeated code reads as a
  diff. Recount the line numbers whenever a listing is edited.
- All demos on a page share one Pyodide runtime, and embeds are editable
  by default.
- Examples must be complete and copyable: include imports, the `State`
  dataclass, and an explicit `start_server(...)` call.
- **Caution**: fence parameters are only stripped from `python drafter`
  fences. On a plain `python` fence, anything after the language renders
  as part of the code block. The planned `test=true` / `repro` markers for
  static fences need plugin support first; until then, do not use them.
  The fence harness (`tests/test_docs_fences.py`) still recognizes them,
  so error-entry repros are blocked on that plugin change.

## The CI gates

Run all of these locally before pushing:

| Gate                 | Command                                        |
| -------------------- | ---------------------------------------------- |
| URL contract + stubs | `uv run python tools/scaffold_docs.py --check` |
| Lint (front-matter, template sections, alt text, fence tags) | `uv run python tools/docs_lint.py` |
| Coverage (symbols vs `drafter.__all__`)                      | `uv run python tools/docs_coverage.py` |
| Fence execution      | `uv run pytest tests/test_docs_fences.py`      |
| Strict build (links, nav, demo compiles, redirects)          | `uv run drafter-docs build --strict` |

The coverage gate is report-only until the reference layer lands (plan
Phase E); after that it becomes blocking.

## Style rules

These rules are the short version of STUDENT_DOCS_PLAN.md §3 and §6:

- Student example code uses only the audience's known constructs: no
  dicts, exceptions, comprehensions, lambdas, or `break`.
- Button and Link targets are route names as strings, no slashes:
  `Button("Feed", "feed")`, never `Button("Feed", feed)`.
- No keyword arguments in basic examples and tutorials: `State(5, 5)`,
  not `State(hunger=5, energy=5)`. Keywords appear only for genuinely
  optional parameters.
- Drafter does not put content on new lines by default. Use `"\n"` where
  a visual break belongs: append to the text before a button row
  (`"... was famous.\n"`), or prefix labels (`"\nA place:"`), or use a
  standalone `"\n"` item before a button.
- Names are plain-English PEP 8; the canonical name glossary keeps
  `State`, `index`, `state` consistent site-wide.
- Tests in examples use `assert_state`, `assert_has`, and `assert_in`, not
  brittle whole-page snapshots.
- Plain language; no "easy", "obvious", or "just"; no em dashes; minimal
  emoji.
- Every image has meaningful alt text; every fence has a language tag.

## Common problems

- **Build error `'index' not found in search paths`**: you wrote
  `template:` in front-matter; the key is `page_type`.
- **Linter reports a page not in the manifest**: add the page to
  `tools/docs_manifest.yaml` first; the manifest is the contract.
- **Strict build fails after moving a page**: update `nav:` in
  `mkdocs.yml` and add a redirect from the old URL in the
  `redirects` plugin block.
- **Front-matter not recognized**: check that the file starts with `---`
  on line 1 and was saved without a byte-order mark (BOM).
