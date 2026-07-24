# JS Testing Plan (Pyodide)

A plan for replacing the "load examples and hope" JS test suite with a layered, comprehensive
suite that actually exercises the machinery — and that eliminates the examples-parity OOM.
Scope: the Pyodide runtime only (Skulpt tests stay as-is).

## Current state (diagnosis)

- One Jest config (`js/jest.config.ts`) with two projects (`pyodide`, `skulpt`). The custom
  environment `js/jest.jsdom-env.cjs` boots **real Pyodide for any test file whose path
  contains the substring "pyodide"** — including pure unit tests that happen to live in
  `__tests__/pyodide/` (e.g. `geolocationBroker.test.ts`), which wastes a full WASM boot.
- The OOM is `js/src/__tests__/pyodide/pyodide.examples-parity.test.ts`: one shared Pyodide
  instance runs every `examples/*.py` (~70 apps) sequentially in a single Jest worker.
  Pyodide's WASM heap only grows; leaked Py/JsProxies accumulate; the worker eventually dies.
  No mitigation exists anywhere (no `workerIdleMemoryLimit`, `maxWorkers`, or heap flags),
  and CI (`.github/workflows/test_and_lint.yml`) marks the whole JS job `continue-on-error`
  because of it — so **no JS test currently blocks anything**.
- `js/src/__tests__/transpiler/transpile.test.ts` is orphaned: matched by neither project's
  `testMatch`, so the transpiler golden-fixture tests never run.
- Known baseline failures: `engine.test.ts` (error text), `timer.test.ts` (restart),
  `pyodide.upload-repro.test.ts` (the "borrowed proxy destroyed" upload bug).
- Playwright ^1.56 is already a devDependency but completely unused. `js/playground/` already
  exists as a manual harness page — a natural seed for e2e.

Key architectural fact shaping the plan: the JS bundle is thin. Routing, rendering, and state
live in Python inside Pyodide; JS owns bootstrapping (`js/src/pyodide.index.tsx`), the
custom-element components, the debug panel, dialogs, config overrides, the HTML→Python
transpiler, and error presentation. So most "machinery" is testable in three distinct tiers,
and only a small core genuinely needs a live interpreter.

## Target architecture: four tiers

```
Tier 1  Pure unit          jsdom-lite, no Pyodide      ~ms/test    runs on every push, blocking
Tier 2  Component/DOM      jsdom + custom elements     ~ms/test    runs on every push, blocking
Tier 3  Pyodide contract   real Pyodide in Jest        ~s/test     small curated set, blocking
Tier 4  Playwright e2e     real browser + real bundle  ~s-min      examples + journeys, sharded
```

The examples-parity suite moves from Tier 3 (where it OOMs) to Tier 4 (where the browser's
process model makes memory a non-issue).

---

## Tier 1 — Pure unit tests (highest ROI, mostly missing today)

No Pyodide, no custom-element upgrade; plain functions in and out. Targets, in priority order:

1. **Transpiler** (`js/src/services/transpiler/compiler.ts` ~950 lines, `parser.ts`) — the
   purest and most valuable surface: deterministic HTML-string → Python-string.
   - First step: **un-orphan** `transpile.test.ts` by adding it to `testMatch`, and confirm the
     golden fixtures in `__tests__/transpiler/documents/` still pass.
   - Then expand: per-tag mapping tests (`img`→`Image`, `input[type=*]`→`TextBox`/`CheckBox`/
     `FileUpload`/date inputs, `table`→`Table`), kwarg remapping (`toPythonKwargKey`: `for`→
     `for_id`, `class`→`classes`, hyphen→underscore), `pythonLiteral` escaping (quotes,
     newlines, unicode), malformed/nested/edge-case HTML, CSS rule extraction.
2. **Error engine** (`js/src/bridge/engine.ts`) — `buildEnvelope` (field-by-field envelope
   shape), `normalizeSystemError` (each error class), `resolvePresentation` (the full
   severity × recoverable policy matrix as a table test), `buildStudentLead`/`buildSteps`
   (NameError/SyntaxError-specific advice). Fixing the known `engine.test.ts` baseline
   failure lands here.
3. **Config overrides** (`js/src/config_overrides.ts`) — all exports against an injected fake
   `Storage`: read/merge/sync round-trips, corrupt-JSON tolerance, `client_server` key
   merging, `DRAFTER_MODIFIED_CONFIGURATION` window global.
4. **Brokers** (`js/src/components/geolocationBroker.ts`, `audioBroker.ts`, `audioGraph.ts`)
   — they already expose `resetForTests()`. Coarse/fine profile caching, in-flight request
   dedup, permission-denied paths, cache expiry. (Move `geolocationBroker.test.ts` out of the
   `pyodide/` folder so it stops booting a WASM runtime for nothing.)
5. **Base element parsers** (`js/src/components/drafterHTMLElement.ts`) —
   `getBooleanAttribute` truthy/falsy matrix, `getNumberAttribute` edge cases,
   `data--drafter-handlers` JSON parsing (valid/invalid/missing).
6. **Runtime scaffolding logic** (`js/src/pyodide.index.tsx`) — the parts extractable without
   a live interpreter:
   - `enqueueRuntimeWork` / execution-chain: serialization order, error in one job doesn't
     poison the chain, reentrancy.
   - Restart-token validation in `createDrafterInstance`'s `drafter-restart-student-code`
     handler (valid token runs, stale/missing token rejected).
   - `toVirtualStudentPath`, package-spec dedup (`requestedPackageSpecs`).
   - If these are closure-private today, export them (or extract to a `runtime-utils.ts`) —
     that refactor is part of this plan.
7. **Telemetry adapters** (`js/src/debug/telemetry/*.ts`) — each `TypedRecord` subtype parsed
   from a captured-from-Python fixture payload (doubles as one half of a contract test, see
   Tier 3).
8. **Debug utils** (`js/src/debug/utils/{text,lists,fs,errors}.ts`) — quick table tests.

## Tier 2 — Component/DOM tests (jsdom, fill gaps + fix baselines)

Existing standalone tests (`timer`, `clock`, `audio`, `map`, `media`, `geolocation`,
`persistence`) are the right shape; extend rather than replace:

- **Timer/clock** (`js/src/components/timer.tsx`): full state machine coverage with fake
  timers — running/paused/finished transitions, `tick`/`finish` event payloads,
  waits-for-`drafter-page-loaded` gating, every `observedAttributes` mutation mid-flight,
  `persistent` behavior. Fix the known "timer restart" baseline failure here.
- **Map** (`map.tsx` + `leaflet-shim.ts`): attribute→Leaflet-call assertions via the recording
  shim (center/zoom/markers updates, marker diffing, height), detach/reattach lifecycle.
- **Media/audio family** (`media.tsx`, `sound.tsx`, `microphone.tsx`, `audioRecorder.tsx`,
  `tone.tsx`, `melody.tsx`): mock `MediaRecorder`/`AudioContext`; assert broker interactions
  and emitted events rather than real audio.
- **Persistence / move-aware lifecycle**: `_drafterBeginMove`/`connectedMoveCallback`
  reparenting semantics — state survives a park-and-restore cycle.
- **Dialogs** (`js/src/dialogs.tsx`): `alertDialog`/`confirmDialog` resolve values, modal
  behavior, drag handles, Escape/close paths.
- **Error rendering**: `renderSystemErrorInRoot` DOM output per envelope category (student
  advice blocks present, traceback collapsed, etc.).
- **Debug panel** (`js/src/debug/index.tsx` + `panels/*.tsx`): instantiate `DebugPanel`
  directly and feed it synthetic `TypedRecord`s — assert state panel, history log, and routes
  panel render each record type. No Pyodide required: the panel's input contract is just
  these records.
- **CustomEvent contracts**: editor "Run" dispatches `drafter-restart-student-code` with
  `{code, _token}`; `drafter-navigate`, `drafter-toggle-debug-mode`, `drafter-evict-persistent`
  dispatch shapes. These pin the JS↔Python control channel from the JS side.
- **enhancements.ts**: copy buttons and expandables.

## Tier 3 — Pyodide integration in Jest (small, curated, blocking)

Keep real-interpreter Jest tests, but only where the *bridge itself* is under test. Target
~8–12 test files, each independently bootable, total runtime a few minutes:

- Boot + hello-world render (`pyodide.test.ts`, keep).
- Forms round-trip: fill/submit via `@testing-library/user-event`, assert Python-rendered
  response (keep `forms-parity`, prune to representative cases).
- Routing/navigation: link clicks, `drafter-navigate`, back/forward via synthetic `popstate`.
- Multi-instance isolation (`pyodide.multi-instance.test.ts`, keep) — two shadow roots, one
  runtime, no state bleed.
- Restart/teardown: `resetPyodideRuntime` → `reset_server_for_root` → no stale listeners
  (JS-side twin of `test_bridge_teardown.py`).
- Persistence across restart (keep).
- Upload: keep `upload-repro` as the regression pin for the borrowed-proxy bug; fixing the
  bug is a prerequisite for making CI blocking.
- **Contract tests**: run a scripted app, capture actual telemetry records crossing
  `debugPanel.handleEvent`, and validate against the `TypedRecord` fixtures used in Tier 1 —
  this catches Python↔JS shape drift in one place.

**What leaves Jest: the examples-parity suite.** Delete
`pyodide.examples-parity.test.ts` once its Playwright replacement (Tier 4) is green.

## Tier 4 — Playwright e2e (real browser; this is where "in practice" lives)

A real browser buys everything jsdom can't do: real WASM memory behavior, shadow DOM, real
event timing, `SharedArrayBuffer` (interrupt), IndexedDB, geolocation emulation, real file
upload/download, `MediaRecorder`, Leaflet layout.

**Infrastructure** (new):
- `js/playwright.config.ts` + `js/e2e/` directory. Chromium-only to start.
- A static server (Playwright `webServer`) serving built `dist/` plus a harness page —
  extend `js/playground/` for this. Serve **COOP/COEP headers** so `SharedArrayBuffer`
  (interrupt machinery) works.
- A small page-object helper: `bootDrafter(page, code)` → returns handles for root,
  debug panel, editor.
- Serve Pyodide + the drafter wheel locally (no CDN) so tests are hermetic and fast.

**Suite A — Examples (replaces the OOM suite).** One spec that shards `examples/*.py` into
batches of ~8; each batch gets a **fresh browser page** (boot Pyodide once per page, run its
batch, close page — memory fully reclaimed by the OS between batches). Same assertions as
today (rendered form contains no `/error/i`; `INTENTIONAL_ERROR_EXAMPLES` inverted), plus
per-example console-error capture. Playwright's `fullyParallel` + `--shard` in CI spreads
batches across workers. This structurally eliminates the OOM instead of tuning around it,
and shrinks `SKIP_EXAMPLES`: matplotlib/PIL/upload examples that couldn't run under
jsdom/NODEFS mostly can in a real browser.

**Suite B — User journeys** (the "exercise the application in practice" core). Pick 5–8 real
apps and drive them like a student would:
- `todo_list.py`: add/complete/delete items, state persists across page navigations.
- `all_forms.py`: every input type filled and submitted, values echoed back correctly.
- A multi-page app: navigate deep, use browser Back/Forward, assert page + state restore.
- An intentional-error app: student-friendly error screen appears, then editor-fix-and-restart
  recovers.

**Suite C — Feature tests that jsdom fundamentally can't cover:**
- File upload end-to-end with a real `File` (regression coverage for the borrowed-proxy bug
  beyond the unit repro).
- Interrupt: start an infinite-loop app, trigger interrupt, assert KeyboardInterrupt surfaces
  and the runtime stays usable (requires the COOP/COEP server).
- Geolocation via `context.setGeolocation` + permission grant → `drafter-current-location`
  renders coordinates.
- Downloads: debug panel "Download state as JSON" produces a real download with valid JSON.
- Map: real Leaflet renders tiles-less but with real layout; markers appear at positions.
- Audio: launch Chromium with fake-media-stream flags; microphone/recorder components reach
  "recorded" state.

**Suite D — Embed/docs host:**
- A page with 2–3 iframes attaching to the shared `DrafterHost` (mirrors the mkdocs
  shared-runtime mode, `window.name` → instance id): all embeds boot, are isolated, and
  detach cleanly on iframe removal/`pagehide`.
- Editor journey: open CodeMirror dialog, edit code, Run (token-validated restart), new
  behavior visible; restart does not duplicate event listeners (stale-listener regression).
- Config overrides: toggle a debug-mode override, reload, assert it persisted via
  `localStorage`.

---

## CI restructuring (`.github/workflows/test_and_lint.yml`)

1. `js-unit`: Tiers 1+2, every push, **blocking from day one** (they're fast and
   deterministic). Add coverage reporting here; ratchet thresholds up as tiers fill in.
2. `js-integration`: Tier 3, every push; blocking once the three baseline failures are fixed.
   Config hardening even before the OOM suite leaves: `maxWorkers: 1` for the pyodide
   project, `workerIdleMemoryLimit: "1.5GB"` (recycles workers between files), and
   `NODE_OPTIONS=--max-old-space-size=4096` as belt-and-braces.
3. `js-e2e`: Tier 4, Playwright with `--shard` (e.g. 4 shards), on PRs to main; upload traces
   on failure. Remove `continue-on-error` from the JS job once Suites A–B are green.

## Jest config changes

- Split the `pyodide` Jest project into `unit` (jsdom env, **no** Pyodide preload) and
  `pyodide-integration` (current env). Kill the "path contains 'pyodide'" substring trigger
  in `jest.jsdom-env.cjs` in favor of an explicit directory (`__tests__/integration/`) or
  env opt-in — that's what let a broker unit test silently boot a WASM runtime.
- Add the orphaned transpiler tests to the `unit` project's `testMatch`.
- Keep the existing shims (`pyodide-shim`, `leaflet-shim`, `css-stub`, `rawTransformer`);
  add fixtures directory `js/src/__tests__/fixtures/telemetry/` for the contract records.

## Phasing

| Phase | Work                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Exit criterion                                                                                   |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 0 ✅   | Jest project split (`unit`/`pyodide`/`skulpt`, Pyodide boot now opt-in via `testEnvironmentOptions`); un-orphaned transpiler + geolocation tests; moved broker test out of `pyodide/`; OOM root-caused and fixed twice over — the harness reset now uses the real bridge teardown (`reset_server_for_root`, was `set_main_server(None)` only, leaving every past example's listeners re-rendering), and `scripts/run-integration-tests.mjs` runs each pyodide file in its own Jest process because leftover timer/animation render loops from one file otherwise OOM later files mid-run; examples-parity sharded into 6 partition files; fixed engine/timer baseline failures, geolocation async drift, transpiler quote style (pulled forward from Phase 2). Remaining known failure: `upload-repro` only (Phase 4) | `npm test` green locally without OOM; unit tier isolated ✅ (81/81 unit, 12/13 integration files) |
| 1 ✅   | Tier 1 pure unit tests: transpiler (`compiler-units`, 115 tests), engine envelope + presentation matrix (`engine-envelope`, 55), config overrides (27), audio brokers/graph (47), base-element attribute parsing (55), execution chain + runtime helpers (`runtime-utils`, 24), telemetry adapters with Python-derived fixtures (23 + `fixtures/telemetry/`), debug utils (23). Unit tier: 81 → **451 tests, ~8s**. CI split into blocking `test-js-unit` + non-blocking `test-js-integration`. 13 suspected production bugs documented in test comments (see test files; headline: transpiler double-stringification of textarea/option values, leading-zero attrs emit invalid Python, `getHandlers()` throws on malformed JSON, `DebugPanel.handleEvent` throws on unknown request ids)                            | `js-unit` CI job added and blocking ✅                                                            |
| 2 🔶  | Done: dialogs (36 tests incl. drag/symbolicId/prompt-validation), event contracts (10 — JS event constants pinned against Python `setup_events` source; editor Run exercised via real CodeMirror), enhancements (10), debug panel rendering (`debug-panel.test.tsx`), sound component. Unit tier: 451 → **580 tests, 24 suites, ~8s**. Two more bugs documented (Escape closes ALL open dialogs; expandable stuck when content ends in `...`). Remaining: timer/clock/map/media-family extensions (microphone, audioRecorder, tone, melody; map marker diffing) | Zero known-failing tests in unit tier ✅ |
| 3 🔶  | Done: `playwright.config.ts` + `e2e/server.mjs` (serves dist, local Pyodide, drafter zip; COOP/COEP verified — `crossOriginIsolated` true, SharedArrayBuffer available, micropip PyPI fetches still work) + `e2e/pages/harness.html` (`bootRuntime`/`runExample` mirroring the jest harness incl. bridge teardown) + `smoke.spec.ts` + `examples.spec.ts` (Suite A: 5 batches of 8 + intentional-errors — **8/8 green in ~11s**, vs ~80s for the jest partitions). `npm run test:e2e` rebuilds the drafter zip first (a stale zip surfaces as baffling Python errors). Remaining: CI job (chromium install + `npm run test:e2e`), then delete the jest examples-parity partitions and un-skip browser-feasible examples (uploads, plotting, PIL) | Examples run green in e2e ✅; OOM suite deleted + `continue-on-error` removed (pending CI proof) |
| 4     | Suites B–D (journeys, browser-only features, embed host); fix upload borrowed-proxy bug; Tier 3 curation + contract tests                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Full JS matrix blocking in CI                                                                    |
| 5     | Coverage thresholds, flake triage, doc a `TESTING.md` for contributors                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Steady state                                                                                     |

Phases 1–2 and 3 are independent and can proceed in parallel.

## Explicit non-goals

- No Skulpt test changes (existing `skulpt` project untouched).
- No visual-regression/screenshot testing initially (can bolt onto Playwright later).
- No cross-browser matrix initially (Chromium only; Firefox/WebKit later if wanted).


## Documented known issues

The tests surfaced 13 suspected production bugs, documented in test comments rather than fixed (each test asserts current behavior, so fixing a bug will flip a clearly-labeled test). The ones I'd triage first:

- Transpiler double-stringifies `<textarea>` content and `<option>` text (students get literal quote characters in their values), leaks extra Button target attrs, silently drops non-numeric width/height, and emits invalid Python for leading-zero numeric attributes (data_code=007).
- getHandlers() on the base element throws an uncaught SyntaxError on malformed handler JSON instead of falling back to {}.
- DebugPanel.handleEvent throws clear out of the adapter on events referencing unknown request ids.
- Type drift between the TS telemetry union and Python emitters: PageVisitEvent appears to be dead, fullType is required in TS but never emitted by Python, and Python's error context carries fields TS doesn't declare.
- Smaller: wordWrap leading blank line, .. not filtered in the pyodide file listing, negative defaults clamped to 0 in getNumberAttribute.