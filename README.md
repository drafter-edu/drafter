# Drafter

A simple Python library for making websites, following good software engineering principles.

## Development

This is the v2 rewrite, so you can use the following

```powershell
git checkout v2-pyodide
```

### Setup (Python via uv)

1. **Prereqs**: Python 3.8+ (recommended 3.11+), Node.js 18+ with npm, and [uv](https://github.com/astral-sh/uv). On Windows PowerShell:

```powershell
winget install astral-sh.uv
```

2. **Clone**:

```powershell
git clone https://github.com/drafter-edu/drafter.git
cd drafter
```

3. **Create the Python environment and install deps** (reads pyproject/uv.lock):

```powershell
uv sync
```

4. **Install JS deps once** (for builds/watchers):

```powershell
cd js
npm install
cd ..
```

5. **Run an example** (uses uv’s virtual env automatically):

```powershell
uv run examples\shop.py
```

If you need the Skulpt engine explicitly, pass `--engine skulpt`.

### build and serve docs

Use the Drafter docs wrapper instead of calling MkDocs directly:

    uv run drafter-docs build
    uv run drafter-docs serve

Optional dev mode:

    uv run drafter-docs build --dev
    uv run drafter-docs serve --dev

In dev mode, the MkDocs Drafter codeblock plugin compiles embedded demos with
Pyodide package style `build` (local package build) instead of the default
`pypi`.

### watch JS assets

To iterate on the JS client and have changes flow into the Python package automatically:

1. In one terminal, run the JS watcher. This rebuilds the TypeScript bridge on every save and copies the output into `src/drafter/assets`:

```powershell
cd js
npm install
npm run dev
```

2. In another terminal, run the JS precompiler. This builds the Skulpt version of the Python Drafter library on every save and copies the output into `src/drafter/assets`:

````powershell
cd js
npm run precompile:watch
```

3. In another terminal, run a local Drafter app so you can see live reloads. For example, using one of the examples:

```powershell
uv run examples\simplest.py
````

Notes:

- The watcher writes bundles to `src/drafter/assets` which the dev server serves from `/assets` and is already included in the server's file-watcher, so connected browsers will auto-reload.
- If you maintain a local Skulpt build, set `SKULPT_DIR` in a top-level `.env` to copy `skulpt.js` and `skulpt-stdlib.js` directly into `src/drafter/assets` on startup (`npm run dev` calls this automatically).

### run tests

- JS tests:

```powershell
cd js
npm run test
```

- Python tests (uses uv env):

```powershell
uv run pytest --verbose --color=yes -vv
```

