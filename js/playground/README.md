# Multiple Drafter Instances Playground

A demo page that runs **several fully-concurrent Drafter apps on one page**,
sharing a single Pyodide runtime. Each instance renders into its own root
element and (by default) its own Shadow DOM, so their ids, styles, and state are
isolated even though the Python interpreter is shared.

## Run it

From `js/`:

```bash
npm run playground        # builds the bundle + assets, then serves on :8777
# then open http://localhost:8777/
```

Or step by step:

```bash
npm run playground:build  # npm run build + node playground/build-playground.mjs
python -m http.server 8777 --directory playground
```

`build-playground.mjs` assembles `playground/__drafter_assets/` (gitignored) from
your **current** sources:

- `js/dist/js/drafter.pyodide.js` — the client bundle
- `js/dist/css/*.css` — stylesheets
- `drafter-pyodide.zip` — the current `src/drafter` package, so local Python
  changes are reflected (mirrors `drafter.builder.build.build_zip`)

Requires `python` on PATH (for the zip) and network access (Pyodide loads from
the jsDelivr CDN).

## How it works

The page calls, once:

```js
await window.Drafter.setupPyodide({ pyodideUrl, systemPackages: [] });
await window.Drafter.mountDrafterRemote("__drafter_assets/drafter-pyodide.zip");
await window.Drafter.patchPythonFeatures();
```

then one `createDrafterInstance(...)` per app:

```js
await window.Drafter.createDrafterInstance({
  rootElementId: "drafter-root--a",
  useShadowDom: true,
  inlineCode: "...student code that calls start_server()...",
});
```

`createDrafterInstance` returns a handle: `{ rootElementId, restart(code?), stop() }`.

### Key pieces that make concurrency work

- **Per-instance server registry** (`drafter.client_server.commands`): each app's
  `start_server()` registers a `ClientServer` keyed by its `root_element_id`
  instead of a single global `MAIN_SERVER`.
- **Scoped DOM lookups**: the bridge resolves `#drafter-body--`, `#drafter-form--`,
  etc. within each instance's shadow root rather than the global document.
- **Serialized setup**: `runStudentCode` runs behind a mutex, because Pyodide is
  single-threaded and setup mutates shared global config — so `Promise.all` of
  several `createDrafterInstance` calls is safe.
- **Isolated namespaces**: each app's code executes in its own module namespace,
  so their route functions / `State` classes don't collide.

## Notes / limitations

- Single-instance production scaffolding is unchanged: it goes through the
  back-compat `startPyodideAppServerSession`, never sets a custom root, and skips
  all of the above (no shadow DOM, main globals) — byte-for-byte as before.
- The global keydown debug hotkey and `document.title` are owned by the primary
  (default-root) instance only.
