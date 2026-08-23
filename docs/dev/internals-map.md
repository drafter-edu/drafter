---
page_type: reference
title: Internals map
audience: D
priority: P2
prereqs: []
symbols: []
outcome: Find the right module fast.
search:
  exclude: true
---

# Internals map

Subsystem by subsystem, where to open the editor. Read
[Architecture](architecture.md) first for how these fit
together; the root `ARCHITECTURE.md` holds the deep detail.

## Python (`src/drafter/`)

| Subsystem | Package | Start with |
| --------- | ------- | ---------- |
| Launch dispatch (web / compile / app mode) | `launch.py` | `start_server` |
| Components | `components/` | `page_content.py` (the `Component` base, `ARGUMENTS`, attribute pipeline), then the family modules (`forms.py`, `text.py`, `layout.py`, `map.py`, `camera.py`, `audio.py`, `timer.py`) |
| Component render planning | `components/planning/` | `render_plan.py` |
| Payloads (Page, Fragment, Update, Redirect) and HTML rendering | `payloads/` | `kinds/`, `renderer.py` |
| Routing, parameter binding, type conversion | `router/` | `parameters/conversion.py` (the converter registry) |
| Client server (routing, state, history, testing) | `client_server/` | `client_server.py`, `commands.py` (the lazy `MAIN_SERVER` and instance registry) |
| Bridge (DOM, form collection, events) | `bridge/` | `bridger.py`, `events.py` (form pipeline, `data-transform` decoding) |
| Dev server and hot reload | `app/` | `app_server.py`, `watcher.py`, `watch_policy.py` (safety checks and safe mode for the watch set) |
| Static site builder | `builder/` | `build.py` (`compile_site`) |
| Site shell and DOM ids | `site/` | `site.py` (`DRAFTER_TAG_IDS`, the `--` suffix convention) |
| Configuration system | `config/` | dataclasses mirroring the CLI flags |
| Value types (Picture, files, Photo) | `data/` | `images.py`, `files.py` |
| Friendly errors | `data/` | `errors.py` (`StudentFacingError`), `error_explainer.py` (the two-tier message tables) |
| Themes and styling helpers | `styling/` | `themes.py` (the theme registry) |
| Deployment-facing config functions | `deploy.py` | `set_website_*`, `set_site_information` |
| Docs pipeline (runnable fences) | `docs/` | the MkDocs plugin and embed assets |

## TypeScript (`js/src/`)

| Subsystem | Location | Notes |
| --------- | -------- | ----- |
| Pyodide bootstrap | `pyodide.index.tsx` | Engine load, micropip, package auto-loading |
| Custom elements | `components/` | One `.tsx` per element (`timer.tsx`, `map.tsx`, `camera.tsx`, ...), each matching its Python `ComponentContract` |
| Debug panel | `debug/` | `index.tsx` composes the tabs |
| CSS | `css/` | Base, debug, deploy, and theme stylesheets |
| Tests | `__tests__/` | Fast unit tests by default; integration and legacy Skulpt suites are separate configs |
| Skulpt (legacy) | `skulpt_bridge/` | Outside the validation baseline; do not modify incidentally |

## Cross-cutting invariants

- Custom-element behavior lives in TypeScript, but the Python
  `ComponentContract` is what the router trusts; the two must
  change together.
- All structural DOM ids end in `--` and come from
  `DRAFTER_TAG_IDS`; nothing else may invent one.
- The bridge stays ignorant of site semantics; logic belongs in
  the client server.
- Friendly error text lives in `error_explainer.py` and at
  `StudentFacingError` raise sites, and the
  [help error index](../help/errors/index.md) mirrors it; keep
  the three in sync.

## Related

- [Architecture](architecture.md): the narrative version.
- [Contributing](contributing.md): running what you just found.
