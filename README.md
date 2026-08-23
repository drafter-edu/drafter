# Drafter

A student-friendly, full-stack web development library for Python, following good software engineering principles.

Drafter lets you build interactive websites out of plain Python functions and dataclasses. You write **route functions** that take the current application **state** and return **pages**; Drafter handles rendering, forms, navigation, history, and debugging. The same program can be run as a local development server or compiled to a fully static site (running Python in the browser via [Pyodide](https://pyodide.org/) or [Skulpt](https://skulpt.org/)) that can be hosted anywhere, such as GitHub Pages.

- **Homepage/Docs:** https://drafter-edu.github.io/drafter/
- **Source:** https://github.com/drafter-edu/drafter
- **License:** MIT
- **Python:** 3.10+

> **Note:** This branch (`v2-pyodide`) is the Drafter **v2** rewrite, currently in beta. See [ARCHITECTURE.md](ARCHITECTURE.md) for a deep dive into the system design.

## Quick start

Install from PyPI:

```bash
pip install drafter
```

Create a file `my_site.py`:

```python
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    message: str

@route
def index(state: State) -> Page:
    return Page(state, [
        "Hello, world!",
        state.message,
        Button("Say goodbye", goodbye),
    ])

@route
def goodbye(state: State) -> Page:
    return Page(state, ["Goodbye!"])

start_server(State("Welcome to my site."))
```

Then run it any of these equivalent ways:

```bash
python my_site.py
drafter my_site.py
python -m drafter my_site.py
```

A local development server starts (by default at `http://localhost:8000`), your browser opens automatically, and the page hot-reloads whenever you save the file.

## How it works

When you run a Drafter program locally, your code actually executes **twice**:

1. **Host side:** Python runs your script normally. When it reaches `start_server(...)`, Drafter starts a local Starlette/uvicorn development server that serves a single page embedding your code, plus a WebSocket connection for hot reload.
2. **Client side:** The served page boots a Python-in-the-browser engine (Pyodide by default, or Skulpt) and re-runs your code there. That in-browser run is the one users actually interact with: routes execute, state updates, and the DOM is updated, all inside the browser.

Because everything runs client-side, `drafter my_site.py --compile` can produce a static build of the same app with no server component at all. This can be deployed on GitHub Pages, Netlify, or any static host.

## Running and building

### Serve (default mode)

```bash
drafter my_site.py [options]
```

Starts the local development server with file watching, hot reload, and the debug panel enabled.

### Compile a static site

```bash
drafter my_site.py --compile [options]
```

Builds a static site (default output: `dist/index.html`) that boots the browser engine and runs your program. Deploy the output directory to any static host.

## Command-line reference

All flags below work with the `drafter` command (and `python -m drafter`). Flags are grouped the same way Drafter's configuration system groups them. Run `drafter --help` for the live list.

### General

| Flag                 | Description                                                                                                         |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `path` (positional)  | Path to your main entry file (e.g., `my_site.py`).                                                                  |
| `--compile`          | Compile the site to static files instead of starting the server.                                                    |
| `--config-file PATH` | Path to a JSON configuration file (repeatable for multiple files). See [Configuration files](#configuration-files). |
| `--verbose`          | Enable verbose output (prints the final resolved configuration at startup).                                         |

### App behavior (server and compile modes)

| Flag                            | Default                       | Description                                                                                                                                                      |
| ------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--engine {skulpt,pyodide}`     | `pyodide`                     | Which Python-in-the-browser engine to use.                                                                                                                       |
| `--prerender-initial-page`      | on                            | Prerender the initial page on startup (useful for SEO and faster first paint).                                                                                   |
| `--asset-directory PATH`        | inferred                      | Directory containing Drafter's static assets. If unspecified, uses the package's bundled `assets/` folder, falling back to `js/dist/` in a development checkout. |
| `--show-filename-as NAME`       | actual name                   | Display name for the main file in the UI, if different from the real filename.                                                                                   |
| `--mount-drafter-locally`       | off                           | Mount the local Drafter source instead of the installed package (local development).                                                                             |
| `--override-asset-url URL`      | off                           | Custom base URL for assets. When building, also names the output assets folder.                                                                                  |
| `--site-title TITLE`            | `Drafter App Server`          | Browser tab title.                                                                                                                                               |
| `--load-packages-automatically` | on                            | Automatically load Python packages detected in the student's code, in addition to `--system-packages` / `--project-packages`.                                    |
| `--system-packages LIST`        | `bakery;pillow`               | Semicolon-separated system packages to load in the browser engine (matplotlib is installed on demand when imported or when `MatPlotLibPlot` is used).            |
| `--project-packages LIST`       | (none)                        | Semicolon-separated project-specific packages to load.                                                                                                           |
| `--pyodide-url URL`             | `https://cdn.jsdelivr.net/pyodide` | Base URL to load Pyodide from; the version and branch are appended.                                                                                        |
| `--pyodide-version VERSION`     | `v314.0.5`                    | Pyodide version to load (e.g. `v314.0.5` or `dev`).                                                                                                              |
| `--pyodide-branch BRANCH`       | `full`                        | Pyodide distribution branch: `full` or `debug`.                                                                                                                  |
| `--pyodide-drafter-path PATH`   | (none)                        | Custom path/URL to the Drafter Pyodide package wheel.                                                                                                            |

### Site rendering and debugging

| Flag                               | Default          | Description                                                                                                      |
| ---------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| `--production`                     | off              | Production mode: disables the debug panel and debug mode.                                                        |
| `--subtle-debug-entry`             | off              | In production, show a subtle control that re-enables the debug panel.                                            |
| `--audit-logging`                  | on               | Enable audit logging of requests/responses.                                                                      |
| `--no-frame`                       | framed           | Remove the browser-window-style frame around the app.                                                            |
| `--theme NAME`                     | `default`        | Site theme. Bundled themes: `default`, `dark`, `none`.                                                           |
| `--server-name NAME`               | `MAIN_SERVER`    | Internal server identifier.                                                                                      |
| `--deploy-image-path PATH`         | (empty)          | Path prefix for images on the deployed site.                                                                     |
| `--external-pages LIST`            | (none)           | Semicolon-separated external links (`URL` or `URL Text`) shown in the generated site (e.g., a GitHub repo link). |
| `--additional-header-content LIST` | (none)           | Semicolon-separated raw HTML strings injected into `<head>`.                                                     |
| `--additional-style-content LIST`  | (none)           | Semicolon-separated inline CSS strings.                                                                          |
| `--additional-css-content LIST`    | (none)           | Semicolon-separated external CSS URLs.                                                                           |
| `--additional-js-content LIST`     | (none)           | Semicolon-separated inline JavaScript strings.                                                                   |
| `--additional-script-content LIST` | (none)           | Semicolon-separated external JS URLs.                                                                            |
| `--use-shadow-dom`                 | off              | Wrap the app in a Shadow DOM to isolate it from page CSS.                                                        |
| `--root-element-id ID`             | `drafter-root--` | ID prefix for Drafter's root element.                                                                            |
| `--newlines-to-br`                 | on               | Convert newlines in text content to `<br>` tags.                                                                 |

### Development server (serve mode only)

| Flag                        | Default     | Description                                                              |
| --------------------------- | ----------- | ------------------------------------------------------------------------ |
| `--port PORT`               | `8000`      | Server port.                                                             |
| `--host HOST`               | `localhost` | Server host address.                                                     |
| `--no-reloader`             | reloader on | Disable the file watcher / auto-reload.                                  |
| `--no-open-browser`         | opens       | Don't automatically open a web browser on start.                         |
| `--no-inline-py`            | inlined     | Load user code via an HTTP request instead of inlining it into the HTML. |
| `--no-serve-adjacent-files` | served      | Don't serve files from the directory next to the user's script.          |

### Static builder (`--compile` mode only)

| Flag                                       | Default      | Description                                                                                                                                                                  |
| ------------------------------------------ | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--output-directory DIR`                   | `dist`       | Directory to write the built site into.                                                                                                                                      |
| `--output-filename NAME`                   | `index.html` | Name of the main generated HTML file.                                                                                                                                        |
| `--create-404 {always,never,if_missing}`   | `if_missing` | Whether to generate a `404.html`.                                                                                                                                            |
| `--zip-output`                             | off          | Zip the output directory after building.                                                                                                                                     |
| `--warn-missing-info`                      | on           | Warn if `set_site_information` was never called.                                                                                                                             |
| `--additional-paths LIST`                  | (none)       | Semicolon-separated extra files to bundle into the built site (e.g., files your code `open`s).                                                                               |
| `--pyodide-package-style {build,cdn,pypi}` | `pypi`       | Where the built page gets the Drafter Pyodide package: a local build, a CDN, or PyPI.                                                                                        |
| `--shared-runtime`                         | off          | Compile the page to attach to a Drafter host in its parent page, sharing one Pyodide runtime across many embedded demos (iframes); boots its own runtime only as a fallback. |

## Environment variables

Every setting can also be provided via environment variables. Boolean variables accept `1`, `true`, or `yes` (case-insensitive) for true; anything else is false. List-valued variables are semicolon-separated.

### General

| Variable              | Type   | Corresponds to                                                    |
| --------------------- | ------ | ----------------------------------------------------------------- |
| `DRAFTER_ENTRY`       | string | Path to the main entry file (the positional `path` argument).     |
| `DRAFTER_MODE`        | string | `start_server` (default) or `compile_site` (same as `--compile`). |
| `DRAFTER_CONFIG_FILE` | list   | Semicolon-separated config file paths.                            |
| `DRAFTER_VERBOSE`     | bool   | Verbose output.                                                   |

### App behavior

| Variable                              | Type   | Corresponds to                  |
| ------------------------------------- | ------ | ------------------------------- |
| `DRAFTER_ENGINE`                      | string | `--engine`                      |
| `DRAFTER_PRERENDER_INITIAL_PAGE`      | bool   | `--prerender-initial-page`      |
| `DRAFTER_ASSET_DIRECTORY`             | string | `--asset-directory`             |
| `DRAFTER_SHOW_FILENAME_AS`            | string | `--show-filename-as`            |
| `DRAFTER_MOUNT_DRAFTER_LOCALLY`       | bool   | `--mount-drafter-locally`       |
| `DRAFTER_OVERRIDE_ASSET_URL`          | string | `--override-asset-url`          |
| `DRAFTER_SITE_TITLE`                  | string | `--site-title`                  |
| `DRAFTER_LOAD_PACKAGES_AUTOMATICALLY` | bool   | `--load-packages-automatically` |
| `DRAFTER_SYSTEM_PACKAGES`             | list   | `--system-packages`             |
| `DRAFTER_PROJECT_PACKAGES`            | list   | `--project-packages`            |
| `DRAFTER_PYODIDE_DRAFTER_PATH`        | string | `--pyodide-drafter-path`        |

### Site rendering and debugging

| Variable                            | Type   | Corresponds to                                       |
| ----------------------------------- | ------ | ---------------------------------------------------- |
| `DRAFTER_SERVER_NAME`               | string | `--server-name`                                      |
| `DRAFTER_IN_DEBUG_MODE`             | bool   | Debug mode (inverse of `--production`).              |
| `DRAFTER_ENABLE_SUBTLE_DEBUG_ENTRY` | bool   | `--subtle-debug-entry`                               |
| `DRAFTER_ENABLE_AUDIT_LOGGING`      | bool   | `--audit-logging`                                    |
| `DRAFTER_FRAMED`                    | string | Whether the app is framed (inverse of `--no-frame`). |
| `DRAFTER_THEME`                     | string | `--theme`                                            |
| `DRAFTER_DEPLOY_IMAGE_PATH`         | string | `--deploy-image-path`                                |
| `DRAFTER_EXTERNAL_PAGES`            | list   | `--external-pages`                                   |
| `DRAFTER_ADDITIONAL_HEADER_CONTENT` | list   | `--additional-header-content`                        |
| `DRAFTER_ADDITIONAL_STYLE_CONTENT`  | list   | `--additional-style-content`                         |
| `DRAFTER_ADDITIONAL_CSS_CONTENT`    | list   | `--additional-css-content`                           |
| `DRAFTER_ADDITIONAL_JS_CONTENT`     | list   | `--additional-js-content`                            |
| `DRAFTER_ADDITIONAL_SCRIPT_CONTENT` | list   | `--additional-script-content`                        |
| `DRAFTER_USE_SHADOW_DOM`            | bool   | `--use-shadow-dom`                                   |
| `DRAFTER_ROOT_ELEMENT_ID`           | string | `--root-element-id`                                  |
| `DRAFTER_NEWLINES_TO_BR`            | bool   | `--newlines-to-br`                                   |

### Development server

| Variable                       | Type   | Corresponds to                                     |
| ------------------------------ | ------ | -------------------------------------------------- |
| `DRAFTER_PORT`                 | int    | `--port` (raises an error if not a valid integer). |
| `DRAFTER_HOST`                 | string | `--host`                                           |
| `DRAFTER_USE_RELOADER`         | bool   | Inverse of `--no-reloader`.                        |
| `DRAFTER_OPEN_BROWSER`         | bool   | Inverse of `--no-open-browser`.                    |
| `DRAFTER_INLINE_PY`            | bool   | Inverse of `--no-inline-py`.                       |
| `DRAFTER_SERVE_ADJACENT_FILES` | bool   | Inverse of `--no-serve-adjacent-files`.            |

### Static builder

| Variable                        | Type   | Corresponds to            |
| ------------------------------- | ------ | ------------------------- |
| `DRAFTER_OUTPUT_DIRECTORY`      | string | `--output-directory`      |
| `DRAFTER_OUTPUT_FILENAME`       | string | `--output-filename`       |
| `DRAFTER_CREATE_404`            | string | `--create-404`            |
| `DRAFTER_ZIP_OUTPUT`            | bool   | `--zip-output`            |
| `DRAFTER_WARN_MISSING_INFO`     | bool   | `--warn-missing-info`     |
| `DRAFTER_ADDITIONAL_PATHS`      | list   | `--additional-paths`      |
| `DRAFTER_PYODIDE_PACKAGE_STYLE` | string | `--pyodide-package-style` |
| `DRAFTER_SHARED_RUNTIME`        | bool   | `--shared-runtime`        |

### Tooling-only variables

| Variable             | Used by          | Description                                                                                                                                                                                   |
| -------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DRAFTER_MKDOCS_DEV` | docs build       | Set to `1` by `drafter-docs --dev`; makes the MkDocs codeblock plugin compile embedded demos with the local package build instead of PyPI.                                                    |
| `DRAFTER_MKDOCS_API` | docs build       | Set to `1` by `drafter-docs --api`; generates the full per-module API reference (mkdocstrings), which is slow. Omitted builds emit a placeholder API page instead.                            |
| `SKULPT_DIR`         | JS build scripts | Path to a local Skulpt build; read from a top-level `.env` file by `npm run dev` / `npm run update-skulpt` / `npm run precompile` to copy `skulpt.js` and `skulpt-stdlib.js` into the assets. |

## Configuration files

Instead of (or in addition to) flags and environment variables, you can put settings in a JSON file and pass it with `--config-file` (repeatable; later files override earlier ones) or `DRAFTER_CONFIG_FILE` (semicolon-separated). The file is keyed by configuration section, with keys matching the dataclass field names:

```json
{
    "bootstrap": { "verbose": true },
    "app_common": { "engine": "pyodide", "site_title": "My Site" },
    "client_server": { "theme": "dark", "in_debug_mode": false },
    "app_server": { "port": 8080, "open_browser": false },
    "app_builder": { "output_directory": "public", "zip_output": true }
}
```

The five sections are `bootstrap`, `app_common`, `client_server`, `app_server`, and `app_builder`, matching the flag groups above.

**Precedence** (lowest to highest):

1. Defaults defined in the code
2. Environment variables
3. Command-line arguments
4. Configuration files
5. Arguments passed to `start_server(...)` and imperative configuration calls in your code (e.g., `set_website_title(...)`)

## Configuring from code

`start_server()` accepts configuration keyword arguments directly, which override everything else:

```python
start_server(State(...), site_title="My Site", theme="dark", port=8080)
```

Commonly used parameters: `site_title`, `theme`, `framed`, `in_debug_mode`, `engine`, `port`, `host`, `open_browser`, `use_reloader`, `inline_py`, `prerender_initial_page`, `asset_directory`, `show_filename_as`, `information`, `verbose`. Any other configuration field can be passed as an extra keyword argument. (The v1 parameters `cdn_skulpt`, `cdn_skulpt_std`, and `cdn_skulpt_drafter` are accepted but ignored, with a warning.)

There are also imperative helpers (importable from `drafter`) that reconfigure the running site:

| Function                                                              | Effect                                                                  |
| --------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `set_website_title(title)`                                            | Set the browser tab title.                                              |
| `set_website_style(style)` / `set_website_theme(theme)`               | Set the theme (`"default"`, `"dark"`, `"none"`; `None` means `"none"`). |
| `set_website_framed(framed)`                                          | Toggle the browser-window frame around the app.                         |
| `hide_debug_information()` / `show_debug_information()`               | Toggle the debug panel.                                                 |
| `add_website_header(html)`                                            | Inject raw HTML into `<head>`.                                          |
| `add_website_css(selector, css)`                                      | Add a CSS rule (or raw CSS if only one argument is given).              |
| `set_site_information(author, description, sources, planning, links)` | Attach site metadata shown on the About page.                           |
| `deploy_site(image_folder)`                                           | Prepare for deployment (hides debug information).                       |

## Development

This section is for working on Drafter itself. The v2 rewrite lives on the `v2-pyodide` branch:

```powershell
git checkout v2-pyodide
```

### Setup (Python via uv)

1. **Prereqs**: Python 3.10+ (3.11+ recommended), Node.js 18+ with npm, and [uv](https://github.com/astral-sh/uv). On Windows PowerShell:

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

5. **Run an example** (uses uv's virtual env automatically):

    ```powershell
    uv run examples\shop.py
    ```

    The [examples/](examples/) directory contains dozens of small apps exercising individual features. Pass `--engine skulpt` if you need the Skulpt engine explicitly (the default is Pyodide).

### Repository layout

| Path                | Contents                                                                                           |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| `src/drafter/`      | The Python package: components, payloads, router, client server, bridge, builder, config system.   |
| `js/`               | The TypeScript client (bridge, debug panel, engines integration), built with tsup into `js/dist/`. |
| `examples/`         | Runnable example applications.                                                                     |
| `tests/`            | Python test suite (pytest).                                                                        |
| `docs/`             | MkDocs documentation sources (see also `docs_legacy/` for the retired v1 pages).                   |
| `tools/`            | Maintenance scripts.                                                                               |
| `Justfile`          | Common dev recipes (`just --list`).                                                                |

Wheels bundle `js/dist/` into `drafter/assets/` at build time (see `pyproject.toml`), so JS must be built before packaging.

### Watch JS assets

To iterate on the JS client and have changes flow into the Python package automatically:

1. In one terminal, run the JS watcher. This rebuilds the TypeScript bridge on every save:

    ```powershell
    cd js
    npm run dev
    ```

2. In another terminal, run the JS precompiler. This rebuilds the Skulpt-compiled version of the Drafter Python library on every save:

    ```powershell
    cd js
    npm run precompile:watch
    ```

3. In another terminal, run a local Drafter app so you can see live reloads:

    ```powershell
    uv run examples\simplest.py
    ```

Notes:

- The watcher writes bundles to `js/dist/`, which the dev server serves from `/assets` and includes in its file watcher, so connected browsers auto-reload.
- If you maintain a local Skulpt build, set `SKULPT_DIR` in a top-level `.env` to copy `skulpt.js` and `skulpt-stdlib.js` into the assets on startup (`npm run dev` does this automatically; `npm run update-skulpt` runs it standalone).

Other useful JS scripts (run from `js/`): `npm run build` (production build), `npm run precompile` (one-shot minified Skulpt precompile), and `npm run playground` (build and serve a standalone playground at `http://localhost:8777`).

### Run tests

- JS tests (fast unit tests are the default; `test:integration` runs the real-Pyodide suites serially with a large heap; `test:skulpt` runs the legacy Skulpt suites, which are currently known-failing and not part of the regular baseline):

    ```powershell
    cd js
    npm run test
    npm run test:integration
    ```

- Python tests (uses uv env):

    ```powershell
    uv run pytest --verbose --color=yes -vv
    ```

- Or run everything plus formatting and linting via [just](https://github.com/casey/just):

    ```powershell
    just validate
    ```

### Build and serve docs

Use the Drafter docs wrapper instead of calling MkDocs directly (it is installed as the `drafter-docs` script and forwards all other arguments to `mkdocs`):

```powershell
uv run drafter-docs build
uv run drafter-docs serve
```

Optional dev mode:

```powershell
uv run drafter-docs build --dev
uv run drafter-docs serve --dev
```

In dev mode, the MkDocs Drafter codeblock plugin compiles embedded demos with Pyodide package style `build` (local package build) instead of the default `pypi`.

Full API reference:

```powershell
uv run drafter-docs build --api
```

Rendering the per-module API reference through mkdocstrings dominates build time, so it is skipped by default and replaced with a placeholder page. Pass `--api` (combinable with `--dev`) when you need the real thing.

## License

MIT — see [LICENSE.txt](LICENSE.txt).
