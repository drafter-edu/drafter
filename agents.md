# Drafter Agents Overview

This note summarizes the moving parts (“agents”) that cooperate to run Drafter in both local dev and in-browser modes. It distills the current README plus what the code does today; if you update behavior, please adjust the links below.

## Runtime roles

-   **ClientServer** (backend state/router/telemetry hub) — owns the `Site`, `Router`, `SiteState`, and `Monitor`, verifies and renders payloads, and attaches errors/warnings. See [src/drafter/client_server/client_server.py](src/drafter/client_server/client_server.py).
-   **Router** — registers routes (auto-adds `index`, `--reset`, `--about`), introspects signatures, injects `state` when expected, converts/validates args (including file uploads). See [src/drafter/router/routes.py](src/drafter/router/routes.py).
-   **Site** — renders the base HTML shell and theme assets, toggled by `in_debug_mode`. See [src/drafter/site/site.py](src/drafter/site/site.py).
-   **Payloads** — `Page`, `Fragment`, `Redirect`, `Update`, etc., encapsulate what the server returns; each can render HTML, update state, send channel messages, and format for history. See [src/drafter/payloads](src/drafter/payloads).
-   **ClientBridge + Client** (browser-side) — updates the DOM, history, and debug panel; mounts click/submit/popstate handlers; executes channel scripts/styles; handles redirects and hotkeys. See [src/drafter/bridge/**init**.py](src/drafter/bridge/__init__.py) and [src/drafter/bridge/client.py](src/drafter/bridge/client.py).
-   **AppServer** (local Starlette dev host) — serves the compiled assets and a live-reloading page for inline Python. See [src/drafter/app/app_server.py](src/drafter/app/app_server.py).

## Startup paths (`start_server`)

-   **Web/Skulpt path**: `start_server` builds a `ClientBridge`, connects it to the event bus, renders the initial `Site`, sets up the debug panel, registers a listener for telemetry, starts the `ClientServer`, issues the initial `index` request, wires navigation, and binds hotkey **Q** to toggle debug mode (re-renders the site). See [src/drafter/launch.py](src/drafter/launch.py).
-   **Local dev path**: when not running in-web, `start_server` calls `serve_app_once` to launch the Starlette/uvicorn dev server with live reload; it will open a browser tab and watch the user script plus packaged assets. See [src/drafter/app/app_server.py](src/drafter/app/app_server.py).

## Request → response pipeline (ClientServer)

1. Record the request and start a timer.
2. Resolve the route; parse arguments (button handling, hidden remaps, type conversions, file upload decoding, optional `state` injection).
3. Execute the route and obtain a payload.
4. Verify payload type and payload-specific rules; render HTML; format for history.
5. Apply state updates (validated against history) and emit telemetry.
6. Collect channel messages; build a `Response` with status/errors/warnings/metadata.
7. On exceptions, wrap them as `VisitError` and return an `ErrorPage` response.

## Payload behaviors

-   **Page** — Renders a list of strings/components to HTML, updates `SiteState`, can inject per-page CSS/JS via before/after channels, and provides history formatting. See [src/drafter/payloads/kinds/page.py](src/drafter/payloads/kinds/page.py).
-   **Fragment** — HTML snippet to replace part of the page without state changes. See [src/drafter/payloads/kinds/fragment.py](src/drafter/payloads/kinds/fragment.py).
-   **Redirect** — Signals client-side navigation with optional arguments; preserves history. See [src/drafter/payloads/kinds/redirect.py](src/drafter/payloads/kinds/redirect.py).
-   **Update** — Applies state changes only (no render). See [src/drafter/payloads/kinds/update.py](src/drafter/payloads/kinds/update.py).
-   Payloads may emit `Message` objects to named channels (e.g., `before` for styles, `after` for scripts) which `ClientBridge` executes on navigation.

## Client-side navigation & UX

-   History is managed via `pushState`/`popstate`; URLs encode the route in the query string. Clicks and submits are intercepted and converted into `Request` objects.
-   Hotkeys: `Client.register_hotkey` listens for ctrl/meta + key double-tap within 600 ms; `start_server` binds **Q** to toggle debug mode.
-   Debug panel is instantiated in-browser when available and can receive telemetry events from the event bus.

## State & persistence

-   `SiteState` tracks the restorable state/history for the session; `Page.get_state_updates` returns new state which is validated (see `verify_page_state_history`) before applying.
-   Default reset/about routes are present; reset clears `SiteState` and redirects to `index`.

## Development workflow (JS assets)

-   Rebuild bridge assets continuously with `npm run dev` from `js/` (copies bundles into `src/drafter/assets`).
-   Rebuild Skulpt/Pyodide variants with `npm run precompile:watch` from `js/`.
-   Run an example app locally, e.g., `python examples\simplest.py`, to exercise live reload.

## Extending or debugging

-   Register new routes through the `Router` API; keep parameter names/types intentional to leverage automatic conversion.
-   To customize error handling or telemetry, extend the `Monitor`/event bus subscribers before `start_server` is invoked.
-   When adding new payload kinds, implement `render`, `verify`, `format`, `get_messages`, and `get_state_updates` to play nicely with the pipeline.
