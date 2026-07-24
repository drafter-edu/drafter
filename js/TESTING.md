# JS Testing Guide

How the JS/TS test suite is organized and how to run it. Planning history and
phase status live in [`../JS_TESTING_PLAN.md`](../JS_TESTING_PLAN.md).

## The four tiers

| Tier | What | Where | Command |
|------|------|-------|---------|
| Unit + component | Pure logic and jsdom custom-element tests, no Pyodide | `src/__tests__/*.test.ts(x)`, `src/__tests__/transpiler/` | `npm test` (~8s) |
| Pyodide integration | Real interpreter in Jest, one process per file | `src/__tests__/pyodide/` | `npm run test:integration` |
| Skulpt | Prebuilt Skulpt bundles from `dist/` | `src/__tests__/skulpt/` | `npm run test:skulpt` |
| Browser e2e | Real Chromium + the built bundle via Playwright | `e2e/*.spec.ts` | `npm run test:e2e` |

`npm run test:all` chains the first three.

## Rules of the road

- **Always run commands from `js/`.** Running `npx playwright test` from the
  repo root resolves a different Playwright install and dies with
  "Playwright Test did not expect test() to be called here".
- **Never run bare `npx jest`** — the npm scripts supply
  `--experimental-vm-modules`, without which ESM imports (jsx-dom etc.) fail.
- **New unit/component tests just go in `src/__tests__/`** — the `unit`
  project globs the whole directory; there is no testMatch list to update.
- **Only put a test in `src/__tests__/pyodide/` if it truly needs the
  interpreter.** That directory opts into a real Pyodide boot per file
  (~10-15s each) via `testEnvironmentOptions.loadPyodide` in
  `jest.config.ts`.
- **Pyodide test files must not share a process.**
  `scripts/run-integration-tests.mjs` runs each in its own Jest process:
  Pyodide's WASM memory is never reclaimed, and leftover timer/animation
  render loops from one file will OOM later files if they share a process.
  `workerIdleMemoryLimit` cannot catch this (it only checks between files).
- **The e2e harness serves a zip of `src/drafter`** built by
  `playground/build-playground.mjs`. `npm run test:e2e` rebuilds it, but if
  you invoke `npx playwright test` directly after changing Python code,
  rebuild it yourself — a stale zip shows up as baffling PythonErrors.
  Changing TS code requires `npm run build` (the harness serves `dist/`).
- **The pyodide npm package ships no wheels.** The e2e server serves
  `node_modules/pyodide/` as `/pyodide/`, but micropip/pillow wheels only
  exist there as a download cache. `npm run test:e2e` runs
  `e2e/prefetch-pyodide-packages.mjs` to populate it; on a fresh checkout
  without that step the boot dies with "No module named 'micropip'".

## E2e layout

- `playwright.config.ts` — Chromium only; `webServer` starts
  `e2e/server.mjs`, which serves the harness pages, `dist/`, a local Pyodide
  distribution, and the drafter zip, all with COOP/COEP headers so pages are
  cross-origin isolated (SharedArrayBuffer works; needed for interrupts).
- `e2e/pages/harness.html` — exposes `bootRuntime()`, `runExample(code)`,
  `resetDrafter()`, and `runInstance(code)` (the instance path registers the
  editor's restart listener). `e2e/pages/multi.html` boots two shadow-DOM
  instances for the embed tests.
- Suites: `examples.spec.ts` (every runnable `examples/*.py`, batched ~8 per
  fresh page; skips are annotated with reasons), `journeys.spec.ts` (form
  round-trip, navigation/history, editor edit-and-run), `features.spec.ts`
  (upload, interrupt, geolocation, download), `embed.spec.ts`
  (same-page shadow-DOM instances), `embed-iframe.spec.ts` (DrafterHost
  iframe embeds — the docs editable-demo shape: shared runtime, per-iframe
  documents, restart/detach), `smoke.spec.ts`.

## Coverage

- `npm run test:coverage` runs the unit tier with coverage over **all of
  `src/`** (not just imported files — see `collectCoverageFrom` in
  `jest.config.ts`, which must stay at the top level: Jest silently ignores
  coverage options inside a project config).
- `coverageThreshold` is a **ratchet**: it sits a few points below the
  measured baseline so regressions fail CI while normal churn passes. Raise
  it as coverage grows; never lower it to make a failing build pass. CI's
  `test-js-unit` job runs the coverage gate.

## Flakes

- Playwright runs with `retries: 0` locally (flakes surface loudly) and
  `retries: 1` in CI, keeping a trace of the failed attempt
  (`test-results/**/trace.zip`, viewable with `npx playwright show-trace`).
- A test that fails intermittently is either a test bug or a product bug —
  don't wrap it in retry loops or widen timeouts to make it pass. The two
  flakes found so far were both product bugs (unreliable first interrupt
  from lazy buffer registration; interrupt orphaning the run when the
  signal lands in the event loop's callback machinery).
- The pyodide integration harness logs `[harness] heapUsed before reset`
  per test to stderr; a heap trend that climbs steeply or a 6GB spike is
  the render-storm/leaked-listener class (see JS_TESTING_PLAN.md).

## Conventions

- `import { describe, expect, test, jest } from "@jest/globals";` and tab
  indentation, matching the existing suites.
- Silence expected console noise with `jest.spyOn(console, ...)` (see
  `engine.test.ts`).
- Mock at the broker/API boundary (`audioBroker`, `geolocationBroker`,
  `MediaRecorder`, the leaflet shim in `src/test-utils/`) rather than deep
  internals.
- If a test documents a suspected production bug (rather than fixing it),
  assert the *current* behavior with a comment saying so — fixing the bug
  should flip a clearly labeled test, not silently pass. (The original
  batch of ~15 such bugs was fixed in July 2026; the pattern remains for
  future finds.)
- Telemetry fixtures in `src/__tests__/fixtures/telemetry/` mirror the
  Python emitters' `to_json()` shapes; the fixtures README records where
  each was derived from. Update both sides together.
